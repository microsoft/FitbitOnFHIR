import os, json
import cmd
import asyncio
from fitbit import Fitbit
from flask import Flask, render_template, url_for, session, redirect
from authlib.integrations.flask_client import OAuth
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceExistsError
from azure.eventhub.aio import EventHubProducerClient
from azure.eventhub import EventData

app = Flask(__name__)

app.config.from_object('config')
app.secret_key = '!secret'
oauth = OAuth(app)

client = oauth.register(name="fitbit")

# Step 1: Bring user to homepage to offer sync service with device cloud (fitbit in this example)
@app.route('/')
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    redirect_uri = url_for('auth', _external=True)
    return oauth.fitbit.authorize_redirect("")

@app.route('/auth')
def auth():
    token = oauth.fitbit.authorize_access_token()
    secretName = session["user"] = token["user_id"]
    secretValue = token["refresh_token"]

    app.secret_key = token["access_token"]

    client = SecretClient(vault_url=app.config["VAULT_URL"], credential=DefaultAzureCredential())

    try:
        client.set_secret(secretName, secretValue)
    except ResourceExistsError:
        # assume user has renabled the service reset the key
        client.begin_delete_secret(secretName)
    

    # sync data with FHIR API using Io[M]T Connector
    loop = asyncio.new_event_loop()
    loop.run_until_complete(sync())

    return "Successful Sync"

@app.route('/sync')
async def sync():
    fit_client = Fitbit(user=session["user"], access_token=app.secret_key)
    result = fit_client.init_sync()
    # Create a producer client to send messages to the event hub.
    # Specify a connection string to your event hubs namespace and
    # the event hub name.
    producer = EventHubProducerClient.from_connection_string(conn_str=app.config["EVENT_HUB_CONN_STR"])
    async with producer:
        # Create a batch.
        event_data_batch = await producer.create_batch()

        for item in result:
            print(item)
            event_data_batch.add(EventData(json.dumps(item, indent = 4)))

        # Send the batch of events to the event hub.
        await producer.send_batch(event_data_batch)

if __name__ == '__main__':
    app.run()


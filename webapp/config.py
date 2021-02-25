import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

## set this ##
VAULT_URL = os.environ["VAULT_URL"]

credential = DefaultAzureCredential()

client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Fitbit Connection

FITBIT_CLIENT_ID = client.get_secret('fitbitClientId').value
FITBIT_CLIENT_SECRET = client.get_secret('fitbitClientSecret').value
FITBIT_ACCESS_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_AUTHORIZE_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_CLIENT_KWARGS = {"scope" : "heartrate activity weight sleep profile"}
FITBIT_API_BASE_URL = "https://api.fitbit.com/1.2/user"

# IoT Hub Connection 
EVENT_HUB_CONN_STR = client.get_secret('eventHubConnStr').value
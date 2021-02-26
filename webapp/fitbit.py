import requests
import config
from datetime import datetime, timedelta, date
from base64 import b64encode, b64decode

base_url = "https://api.fitbit.com/1.2/user"
refresh_url = "https://api.fitbit.com/oauth2/token"

class FitbitOAuth:
    def __init__(self, refresh_token):
        self.refresh_token = refresh_token
    
    def refresh_authentication(self):
        headers = {"Authorization" : f"Basic {self.get_headers()}" , "Content-type" : "application/x-www-form-urlencoded"}
        params = {"grant_type" : "refresh_token", "refresh_token" : self.refresh_token}
        response = requests.post(refresh_url, params=params, headers=headers)
        return response.json()

    def get_headers(self):
        auth_header_raw = f'{config.FITBIT_CLIENT_ID}:{config.FITBIT_CLIENT_SECRET}'.encode()
        auth_header_b64 = b64encode(auth_header_raw).decode('ascii')
        return auth_header_b64    

class Fitbit:
    def __init__(self, user, access_token):
        self.user = user
        self.access_token = access_token
    
    def make_api_call(self, endpoint):
        url = f"{base_url}/{self.user}/{endpoint}"
        response = requests.get(url, headers={'Authorization' : f"Bearer {self.access_token}"})
        return response.json()
    
    def get_weight(self, period="max"):
        endpoint = f"body/weight/date/today/{period}.json"
        response =  self.make_api_call(endpoint)
        response["payload"] = response.pop("body-weight")
        for item in response["payload"]:
            item["deviceId"] = self.user
            item["weight"] = item.pop("value")
        return response
    
    def get_sleep(self, date="today"):
        endpoint = f"/sleep/date/{date}.json"
        response = self.make_api_call(endpoint)
        try:
            result = {"payload" : [item for item in response["sleep"][0]["levels"]["data"]]}
            for item in result["payload"]:
                item["deviceId"] = self.user
        except IndexError:
            return {"payload": "NA"}
        except KeyError:
            return {'payload': 'NA'}
        return result
    
    def get_profile(self):
        endpoint = "profile.json"
        return self.make_api_call(endpoint)
    
    def get_heart_rate_standard(self, period="1m"):
        endpoint = f"activities/heart/date/today/{period}.json"
        return self.make_api_call(endpoint)
    
    def get_heart_rate_intraday(self, date="2021-01-23", detail_level="1sec"):
        ''' This function can only be called if you gain access from Fitbit - refer to docs for more info '''
        endpoint = f"activities/heart/date/{date}/1d/{detail_level}.json"
        return self.make_api_call(endpoint)

    def get_steps(self, date="today", period="1y"):
        endpoint = f"activities/steps/date/{date}/{period}.json"
        response = self.make_api_call(endpoint)
        result = {}
        result["payload"] = response.pop("activities-steps")
        for item in result["payload"]:
            item["deviceId"] = self.user
            item["steps"] = item.pop("value")
        return result
    
    def init_sync(self):
        result = []
        result.append(self.get_steps())
        result.append(self.get_weight())
        dates = list(self.datetime_range(start=datetime.now()-timedelta(weeks=10), end=datetime.today()))
        for date in dates:
            sleep = self.get_sleep(date=date)
            if sleep != {'payload': 'NA'}:
                result.append(sleep)
        
        return result

    def datetime_range(self, start=None, end=None):
        span = end - start
        for i in range(span.days + 1):
            result = start + timedelta(days=i)
            yield result.strftime('%Y-%m-%d')





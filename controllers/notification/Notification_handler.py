import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service-account.json")
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']
PROJECT_ID = 'cd-automation-b92ca'

def send_app_notification(device_token, title, message):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        credentials.refresh(Request())
        access_token = credentials.token

        fcm_url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'

        payload = {
            "message": {
                "token": device_token,
                "notification": {
                    "title": title,
                    "body": message
                },
                "data": {
                    "click_action": "FLUTTER_NOTIFICATION_CLICK"
                },
                "android": {
                    "notification": {
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                        "icon": "app_icon",
                        "color": "#FFB300"
                    }
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8",
        }

        response = requests.post(fcm_url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            print(f"✅ Notification sent to token: {device_token}")
        else:
            print(f"❌ Failed to send notification to token: {device_token}")
            print("Response:", response.status_code, response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

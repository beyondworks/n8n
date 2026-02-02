
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notion_config.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file not found at {CONFIG_FILE}")
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def main():
    config = load_config()
    if not config:
        return

    client_id = config.get('email_client_id')
    client_secret = config.get('email_client_secret')

    if not client_id or not client_secret:
        print("Error: email_client_id or email_client_secret missing in notion_config.json")
        return

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("Starting new authentication flow...")
            # Create a client config dictionary on the fly
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials for the next run
        print(f"Saving token to {TOKEN_FILE}...")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("Token saved successfully! You can now send emails.")

if __name__ == '__main__':
    main()

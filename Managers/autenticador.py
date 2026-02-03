""" GoogleOauth class """
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from Utils.secrets import Secrets

class GoogleOAUTH:
    """
    Google API Service - Creates the authenticator object
    Use the specific Service Manager for your API calls (SheetManager, ScriptManager...)
    """
    def __init__(self, save_credentials=True):
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/script.scriptapp'
        ]
        self.creds = None

        # Check if token.json file exists and load credentials
        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", self.scopes)

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        'web': {
                            'client_id': Secrets.GOOGLE_OAUTH2_CLIENT_ID,
                            'project_id': Secrets.GOOGLE_OAUTH2_PROJECT_ID,
                            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                            'token_uri': 'https://oauth2.googleapis.com/token',
                            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                            'client_secret': Secrets.GOOGLE_OAUTH2_CLIENT_SECRET
                        }
                    },
                    self.scopes
                )
                if save_credentials:
                    flow.run_local_server(
                        port=3000,
                        success_message='Você foi autenticado com sucesso. Pode fechar essa janela',
                        access_type='offline',
                        prompt='consent'
                    )
                else:
                    flow.run_local_server(
                        port=3000,
                        success_message='Você foi autenticado com sucesso. Pode fechar essa janela',
                        access_type='offline'
                    )
                self.creds = flow.credentials

                # Save the credentials
                if save_credentials:
                    with open("token.json", "w", encoding="utf-8") as token:
                        token.write(self.creds.to_json())


        self.oauth2_client = self.creds
        self.oauth2_data = build('oauth2', 'v2', credentials=self.oauth2_client)
        self.oauth2_sheets = build("sheets", "v4", credentials=self.oauth2_client)
        self.oauth2_drive = build("drive", "v3", credentials=self.oauth2_client)
        self.oauth2_gmail = build("gmail", "v1", credentials=self.oauth2_client)
        self.oauth2_scripts = build('script', 'v1', credentials=self.oauth2_client)

    def get_user_email(self):
        """
        Returns the email of the logged-in user.
        """
        user = self.oauth2_data.userinfo().get().execute()
        return user['email']

    def get_oauth2_sheets(self):
        """
        Used by Managers to make api calls with Google Sheets.
        """
        return self.oauth2_sheets

    def get_oauth2_drive(self):
        """
        Used by Managers to make api calls with Google Drive.
        """
        return self.oauth2_drive

    def get_oauth2_gmail(self):
        """
        Used by Managers to make api calls with Google Mail.
        """
        return self.oauth2_gmail

    def get_oauth2_scripts(self):
        """
        Used by Managers to make api calls with Google Script.
        """
        return self.oauth2_scripts

from Managers.autenticador import GoogleOAUTH

class GmailManager:
    """Handle API calls on a instance of google_oauth"""
    def __init__(self, google_oauth: GoogleOAUTH):
        self.oauth2_drive = google_oauth.get_oauth2_gmail()
        self.user_email = google_oauth.get_user_email()

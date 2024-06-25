import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account

def verify_credentials():
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])

    # Verify the credentials by making a simple API call
    auth_request = Request()
    scoped_credentials.refresh(auth_request)
    print("Credentials are valid and authenticated.")

if __name__ == "__main__":
    verify_credentials()

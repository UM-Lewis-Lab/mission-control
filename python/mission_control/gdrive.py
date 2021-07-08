import os
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = (
    Path(os.getenv("GDRIVE_CREDENTIALS", "/secrets/gdrive-credentials.json"))
    .expanduser()
    .resolve()
)
TOKEN_PATH = (
    Path(os.getenv("GDRIVE_TOKEN", "/secrets/gdrive-token.json")).expanduser().resolve()
)


def authenticate(credentials_path: Path, token_path: Path):
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds


def load_credentials(credentials_path: Path, token_path: Path):
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = authenticate(
                credentials_path=credentials_path, token_path=token_path
            )
    return creds


def connect(credentials_path: Path = CREDENTIALS_PATH, token_path: Path = TOKEN_PATH):
    return build(
        "drive", "v3", credentials=load_credentials(credentials_path, token_path)
    )

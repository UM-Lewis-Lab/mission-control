import os
from pathlib import Path

from googleapiclient.discovery import build, Resource as GoogleResource
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_PATH = (
    Path(os.getenv("GDRIVE_CREDENTIALS", "/run/secrets/gdrive-credentials.json"))
    .expanduser()
    .resolve()
)
TOKEN_PATH = (
    Path(os.getenv("GDRIVE_TOKEN", "/run/secrets/gdrive-token.json"))
    .expanduser()
    .resolve()
)


class GDriveClient:
    def __init__(self, drive_service: GoogleResource):
        self.service = drive_service

    def search(self, query: str):
        """Returns a list of files and/or folders matching `query`.
        See https://developers.google.com/drive/api/v3/search-files"""
        results = []
        page_token = None
        while True:
            response = (
                self.service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )
            results.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
        return results

    def find(self, query: str, fail_if_missing=False, **kwargs):
        """Perform a search, assert that it only matches one item, and then return the item.
        Returns `None` if no items match the query unless `fail_if_missing` is `True`
        (in which case an error is raised)."""
        search_result = self.search(query, **kwargs)
        if len(search_result) == 1:
            return search_result[0]
        elif len(search_result) > 1:
            raise ValueError(
                f"\nQuery: \n{query}\n\n matches more than on file / folder"
            )
        elif fail_if_missing:
            raise FileNotFoundError(
                f"\nQuery: \n{query}\n\n does not match any files / folders"
            )
        return None

    def create_folder(self, name: str) -> str:
        """Creates a folder with `name` and returns its ID."""
        file_metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        file = self.service.files().create(body=file_metadata, fields="id").execute()
        return file.get("id")

    def get_folder(self, name: str, create=True) -> str:
        """Returns the ID of the folder with `name`."""
        search_result = self.find(
            f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder'",
            fail_if_missing=False,
        )
        if search_result is not None:
            return search_result.get("id")
        elif create:
            return self.create_folder(name)
        else:
            raise FileNotFoundError(f"Folder: '{name}' not found")

    def upload(
        self,
        local_path: Path,
        name: str,
        folder_name=None,
        folder_id=None,
        mime_type="application/octet-stream",
    ) -> str:
        """Upload a file from `local_path` to GDrive with `name` and return its ID.
        If `folder_id` or `folder_name` is specified, the file will be uploaded inside that folder."""
        file_metadata = {"name": name}
        if folder_name and not folder_id:
            folder_id = self.get_folder(folder_name)

        query = f"name = '{name}' and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        if folder_id:
            file_metadata["parents"] = [folder_id]
            query += f" and '{folder_id}' in parents"

        # Check if the file already exists
        if self.find(query, fail_if_missing=False) is not None:
            message = f"File with name '{name}' already exists"
            if folder_id:
                message += f"in folder '{folder_id}'"
            raise FileExistsError(message)

        media = MediaFileUpload(
            str(local_path.expanduser().resolve()), mimetype=mime_type
        )
        file = (
            self.service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return file.get("id")

    def download(self, download_path: Path, file_id: str = None, file_name: str = None):
        """Download a file from GDrive to a `download_path`"""
        if file_name and not file_id:
            # If a path was provided, get the file id from the path.
            file_id = self.find(
                f"name = '{file_name}' and mimeType != 'application/vnd.google-apps.folder' and trashed = false",
                fail_if_missing=True,
            ).get("id")
        if file_id is None:
            raise ValueError("Please provide `file_id` or `file_name`")
        request = self.service.files().get_media(fileId=file_id)
        with download_path.expanduser().resolve().open("wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print("Downloading ", int(status.progress() * 100), "%")


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


def connect(
    credentials_path: Path = CREDENTIALS_PATH, token_path: Path = TOKEN_PATH
) -> GDriveClient:
    service = build(
        "drive", "v3", credentials=load_credentials(credentials_path, token_path)
    )
    return GDriveClient(service)

import os
import sys
import multiprocessing as mp
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build, Resource as GoogleResource
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .util import backup_timestamp

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
    def __init__(self, drive_service: GoogleResource, root_folder_name: str):
        self.service = drive_service
        self.root_folder = (
            None  # `self.get_folder()` assumes `self.root_folder` is defined
        )
        self.root_folder = self.get_folder(root_folder_name)

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

    def rename(self, item_id: str, new_name: str):
        self.service.files().update(fileId=item_id, body=dict(name=new_name)).execute()

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Creates a folder with `name` and returns its ID."""
        file_metadata = dict(
            name=name,
            mimeType="application/vnd.google-apps.folder",
        )
        parent_id = parent_id or self.root_folder
        if parent_id:
            file_metadata.update(parents=[parent_id])
        file = self.service.files().create(body=file_metadata, fields="id").execute()
        return file.get("id")

    def get_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        create=True,
        fail_if_missing=False,
    ) -> Optional[str]:
        """Returns the ID of the folder with `name`."""
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        parent_id = parent_id or self.root_folder
        if parent_id is not None:
            query += f" and '{parent_id}' in parents"
        search_result = self.find(
            query,
            fail_if_missing=fail_if_missing,
        )
        if search_result is not None:
            return search_result.get("id")
        elif create:
            return self.create_folder(name, parent_id=parent_id)
        else:
            return None

    def upload(
        self,
        local_path: Path,
        name: str,
        folder_name=None,
        folder_id=None,
        mime_type="application/octet-stream",
        replace=False,
    ) -> str:
        """Upload a file from `local_path` to GDrive with `name` and return its ID.
        If `folder_id` or `folder_name` is specified, the file will be uploaded inside that folder."""
        if folder_name and not folder_id:
            folder_id = self.get_folder(folder_name)
        if not folder_id:
            folder_id = self.root_folder

        query = f"name = '{name}' and mimeType != 'application/vnd.google-apps.folder'"
        query += f" and trashed = false and '{folder_id}' in parents"

        # Check if the file already exists
        existing_file = self.find(query, fail_if_missing=False)
        if existing_file is not None:
            existing_file = existing_file.get("id")
            if replace:
                self.service.files().delete(fileId=existing_file).execute()
            else:
                self.rename(existing_file, f"{name}-{backup_timestamp()}")

        # Upload the new file.
        file_metadata = dict(name=name, parents=[folder_id])
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
            if not credentials_path.parent.exists():
                credentials_path.parent.mkdir(parents=True)
            creds = authenticate(
                credentials_path=credentials_path, token_path=token_path
            )
    return creds


def connect(
    credentials_path: Path = CREDENTIALS_PATH,
    token_path: Path = TOKEN_PATH,
    root_folder_name: str = "mission-control",
) -> GDriveClient:
    service = build(
        "drive", "v3", credentials=load_credentials(credentials_path, token_path)
    )
    return GDriveClient(service, root_folder_name=root_folder_name)


def backup_handler(q: mp.Queue, root_folder_name: str):
    gdrive = connect(root_folder_name=root_folder_name)
    data = q.get(block=True)
    while data is not None:
        gdrive.upload(**data)
        data = q.get(block=True)


class BackupService:
    def __init__(
        self,
        gdrive: GDriveClient,
        project_name: str,
        experiment_name: str,
        run_name: str,
        overwrite=False,
        root_folder_name: str = None,
    ):
        self.gdrive = gdrive
        self.finished = False

        self.project_folder = self.gdrive.get_folder(project_name)
        self.experiment_folder = self.gdrive.get_folder(
            experiment_name, parent_id=self.project_folder
        )
        if not overwrite:
            # Check if a run folder exists already and rename it.
            existing_run_folder = self.gdrive.get_folder(
                run_name, parent_id=self.experiment_folder, create=False
            )
            if existing_run_folder:
                self.gdrive.rename(
                    existing_run_folder, f"{run_name}-{backup_timestamp()}"
                )

        self.run_folder = self.gdrive.get_folder(
            run_name, parent_id=self.experiment_folder
        )
        self.artifact_folder = self.gdrive.get_folder(
            "artifacts", parent_id=self.run_folder
        )

        self.queue = mp.Queue()
        self.process = mp.Process(
            target=backup_handler, args=(self.queue, root_folder_name)
        )
        self.process.start()

    def backup(self, data: dict):
        self.queue.put(data)

    def finish(self):
        if not self.finished:
            self.queue.put(None)
            self.queue.close()
            self.process.join()
            self.process.close()
            self.finished = True

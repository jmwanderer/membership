"""
Utility functions for accessing files on Google Drive
"""


import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from googleapiclient.http import MediaIoBaseDownload  # type: ignore
from googleapiclient.http import MediaIoBaseUpload   # type: ignore
from googleapiclient.http import MediaFileUpload   # type: ignore

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = None


def login():
    """
    Handle login and credentials.
        If creds has been saved in token.json, use that.
    """
    global creds
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

def get_folder_id(drive, folder_name):
    """
    Return ID of a single folder matching folder_name
    """
    folderId = (
        drive.files()
        .list(
            q="mimeType = 'application/vnd.google-apps.folder' and name = '"
            + folder_name
            + "'",
            pageSize=10,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, files(id, name, webViewLink)",
        )
        .execute()
    )

    # this gives us a list of all folders with that name
    folderIdResult = folderId.get("files", [])
    # however, we know there is only 1 folder with that name, so we just get the id of the 1st item in the list
    if len(folderIdResult) == 0:
        print(f"Error: no folders found for '{folder_name}'")
        return None
    fid = folderIdResult[0].get("id")
    return fid


def get_file_id(drive, folder_id, filename) -> str|None:
    query = f"name='{filename}' and '{folder_id}' in parents"
    results = drive.files().list(q=query).execute()
    files = results.get('files', [])
    if files is None or len(files) == 0:
        print(f"file {filename} in {folder_id} not found")
        return None
    if len(files) != 1:
        print(f"Found more than 1 ({len(files)}) for {filename}")
        return None
    return files[0]['id']


def get_file_list(drive, folder_name):
    """
    Return the list of files in a folder.
    """
    fid = get_folder_id(drive, folder_name)
    if fid is None:
        return []

    results = (
        drive.files()
        .list(
            q="'" + fid + "' in parents and mimeType = 'application/pdf'",
            pageSize=1000,
            fields="nextPageToken, files(id, name, webViewLink)",
        )
        .execute()
    )
    items = results.get("files", [])
    return items

def move_file(drive, file_id, new_folder_id):
    # Get existing parents / folders
    file = drive.files().get(fileId=file_id, fields='parents').execute()
    previous_parents = file.get('parents', [])
    body = {
        'addParents': new_folder_id,
        'removeParents': ','.join(previous_parents)
    }
    # Update files parent folder
    drive.files().update(fileId=file_id, 
                         addParents=new_folder_id,
                         removeParents=','.join(previous_parents),
                         fields='id, parents'
                         ).execute()
    print(f"Moved {file_id} to {new_folder_id}")

def update_csv_file(drive, file_id, name: str):
    media = MediaFileUpload(name, mimetype='text/csv')
    updated_file = drive.files().update(
        fileId=file_id,
        media_body=media,
        fields="id").execute()
    return updated_file

def upload_csv_file(drive, folder_id: str, filename: str, name: str):
    media = MediaFileUpload(name, mimetype='text/csv')
    metadata = {'name': filename, 
                'parents': [folder_id]}
    updated_file = drive.files().create(
        body=metadata,
        media_body=media,
        fields="id").execute()
    return updated_file

def download_file(drive, file_id) -> io.BytesIO:
    """
    Get a GDrive file by ID and return a bytes stream
    """

    request = drive.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return file

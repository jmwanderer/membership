import os.path
import io
import pickle
import csv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import attestation_pdf

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
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

def get_file_list(drive, folder_name):
    """
    Return the list of files in a folder.
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
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )

    # this gives us a list of all folders with that name
    folderIdResult = folderId.get("files", [])
    # however, we know there is only 1 folder with that name, so we just get the id of the 1st item in the list
    fid = folderIdResult[0].get("id")

    results = (
        drive.files()
        .list(
            q="'" + fid + "' in parents",
            pageSize=1000,
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    items = results.get("files", [])
    return items

def download_file(drive, file_id) -> io.BytesIO():
    request = drive.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return file
        


def main():
    attestations = []

    login()
    drive = build("drive", "v3", credentials=creds)
    folder_name = "2025 Household Attestations and Household Waivers"
    files = get_file_list(drive, folder_name)
    if not files:
        print("No files found.")
    else:
        print("Files:")
        for file in files:
            print(f"{file['name']} ({file['id']})")
            file_data = download_file(drive, file['id'])
            attestation = attestation_pdf.parse_attestation(file_data)
            attestation.file_name = file['name']
            print(attestation)
            attestations.append(attestation)

    with open("attestations.pkl", "wb") as f:
        pickle.dump(attestations, f)
    

def main1():
    with open("attestations.pkl", "rb") as f:
        attestations = pickle.load(f)
    for attestation in attestations:
        print(attestation)
        print()


if __name__ == "__main__":
    main1()

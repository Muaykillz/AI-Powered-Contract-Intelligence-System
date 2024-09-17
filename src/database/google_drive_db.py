from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io
import os
import streamlit as st
from src.utils.config import load_environment_variables

load_environment_variables()

SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')

@st.cache_resource
def get_drive_service():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        # Test the credentials with a simple API call
        service.files().list(pageSize=1).execute()
        return service
    except Exception as e:
        st.error(f"Error authenticating with Google Drive: {str(e)}")
        print(f"Detailed error: {e}")
        print(f"Service account file path: {os.path.abspath(SERVICE_ACCOUNT_FILE)}")
        print(f"SCOPES: {SCOPES}")
        print(f"FOLDER_ID: {FOLDER_ID}")
        return None

def save_to_google_drive(uploaded_file):
    service = get_drive_service()
    if service is None:
        return None

    file_metadata = {
        'name': uploaded_file.name,
        'mimeType': uploaded_file.type,
        'parents': [FOLDER_ID]
    }

    file_io = io.BytesIO(uploaded_file.getvalue())
    media = MediaIoBaseUpload(file_io, mimetype=uploaded_file.type)

    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()

    return file.get('id')

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_files_from_drive():
    service = get_drive_service()
    
    results = service.files().list(
        q=f"'{FOLDER_ID}' in parents",
        pageSize=1000,
        fields="nextPageToken, files(id, name, mimeType, size, modifiedTime)"
    ).execute()
    
    files = results.get('files', [])
    
    return [{
        'id': file['id'],
        'name': file['name'],
        'type': '📄',
        'size': f"{int(file['size']) / 1024:.2f} KB" if 'size' in file else 'N/A',
        'modified': file['modifiedTime']
    } for file in files]

def download_file(file_id):
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    file.seek(0)
    return file
import os
import datetime
import time
import io
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from bikini import Create_Service

CLIENT_SECRET_FILE = '/Users/tim/Documents/projects/MailMerge/GDocsOauth/credentials.json'
API_SERVICE_NAME = 'docs'
API_VERSION = 'v1'
SCOPES = ['https://www.googleapis.com/auth/documents',
          'https://www.googleapis.com/auth/drive']

"""
Step 1. Create Google API Service Instances
"""
# Google Docs instance
service_docs = Create_Service(
    CLIENT_SECRET_FILE, 
    'docs', 'v1', 
    ['https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive']
)
time.sleep(2)

# Google Drive instance
service_drive = Create_Service(
    CLIENT_SECRET_FILE,
    'drive',
    'v3',
    ['https://www.googleapis.com/auth/drive']
)
time.sleep(2)

# Google Sheets instance
service_sheets = Create_Service(
    CLIENT_SECRET_FILE,
    'sheets',
    'v4',
    ['https://www.googleapis.com/auth/spreadsheets']
)
time.sleep(2)


template_document_id = '1ydxJ1j9q2eJGqEfT4wiXXGSkkcThtqQi9maSRr6RK9Q' #2line template
google_sheets_id = '1QAhRqpFaaDsjuNo1rcXWoHyylnPmVuTiGdhRJl3_JkA' #2line source
folder_id = '1E408UgPuVXFmoEUntDPhqJX5SvS5eOxg' # None --> save in the parent folder

responses = {}

"""
Step 2. Load Records from Google Sheets
"""
worksheet_name = 'list2Lines' #2 line source
responses['sheets'] = service_sheets.spreadsheets().values().get(
    spreadsheetId=google_sheets_id,
    range=worksheet_name,
    majorDimension='ROWS',
).execute()

columns = responses['sheets']['values'][0]
records = responses['sheets']['values'][1:]


"""
Step 3. Iterate Each Record and Perform Mail Merge
"""

def mapping(merge_field, value=''):
    json_representation = {
        'replaceAllText': {
            'replaceText': value,
            'containsText': {
                'matchCase': 'true',
                'text': '{{{{{0}}}}}'.format(merge_field)
            }
        }
    }
    return json_representation

for record in records:
    print('Processing record {0}...'.format(record[2]))
    # Copy template doc file as new doc file
    document_title = 'SOW for {0}'.format(record[2])

    responses['docs'] = service_drive.files().copy(
        fileId=template_document_id,
        body={
            'parents': [folder_id],
            'name': document_title
        }
        
    ).execute()
    document_id = responses['docs']['id']
    
    # Update Google Docs document (not template file)
    merge_fields_information = [mapping(columns[indx], value) for indx, value in enumerate(record)]

    service_docs.documents().batchUpdate(
        documentId=document_id,
        body={
            'requests': merge_fields_information
        }
    ).execute()

    """
    Export Document as PDF
    """
    PDF_MIME_TYPE = 'application/pdf'
    byteString = service_drive.files().export(
        fileId=document_id,
        mimeType=PDF_MIME_TYPE
    ).execute()

    media_object = MediaIoBaseUpload(io.BytesIO(byteString), mimetype=PDF_MIME_TYPE)
    service_drive.files().create(
        media_body=media_object,
        body={
            'parents': [folder_id],
            'name': '{0} (PDF).pdf'.format(document_title)
        }
    ).execute()
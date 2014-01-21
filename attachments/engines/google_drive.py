import os
import datetime
import httplib2
import json
import urllib
import tempfile

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import FlowExchangeError
from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build
from apiclient.http import MediaFileUpload, HttpError

from attachments import app_settings
from base import BaseEngine

FOLDER_MIME = 'application/vnd.google-apps.folder'

def get_flow():
    flow = OAuth2WebServerFlow(
        app_settings.GOOGLE_DRIVE_CLIENT_ID,
        app_settings.GOOGLE_DRIVE_CLIENT_SECRET,
        ' '.join(app_settings.GOOGLE_DRIVE_SCOPES),
        redirect_uri=app_settings.GOOGLE_DRIVE_REDIRECT_URL,
        # None, # user_agent
        #"https://accounts.google.com/o/oauth2/auth",
        #"https://accounts.google.com/o/oauth2/token",
        )
    return flow

def get_authorization_url(user_id, state, flow=None):
    if not flow:
        flow = get_flow()

    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    flow.params['user_id'] = user_id
    flow.params['state'] = state
    # u'code': [u'4/rdMBTpmiemBITpy12bTCMHlEOOe6.slmVgVOMScYcshQV0ieZDArYbERicgI']

    return flow.step1_get_authorize_url() #app_settings.GOOGLE_DRIVE_REDIRECT_URL)

def get_new_credentials(auth_code, flow=None):
    if not flow:
        flow = get_flow()

    return flow.step2_exchange(auth_code)

def get_stored_credentials(access_token, refresh_token):
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    cred = OAuth2Credentials(
            access_token=access_token,
            client_id=app_settings.GOOGLE_DRIVE_CLIENT_ID,
            client_secret=app_settings.GOOGLE_DRIVE_CLIENT_SECRET,
            refresh_token=refresh_token,
            token_expiry=tomorrow.strftime('%Y-%m-%dT%H:%M:%S'),
            token_uri="https://accounts.google.com/o/oauth2/token",
            user_agent=None,
            )
    return cred

def get_http_client(access_token, refresh_token):
    cred = get_stored_credentials(access_token, refresh_token)
    client = httplib2.Http()
    return cred.authorize(client)

def get_service(access_token, refresh_token):
    client = get_http_client(access_token, refresh_token)
    return build('drive','v2',http=client)

def get_or_create_collection(service, title, parent_id=None):
    # Check existing collection
    search_query = "title='%s' and mimeType='%s'" % (title, FOLDER_MIME)
    if parent_id:
        search_query += " and '%s' in parents" % parent_id
    search = service.files().list(q=search_query).execute()

    # Checks which found item is the right one
    for item in search['items']:
        if not item['parents']:
            continue

        # Returns if exists and is the valid one
        if item['parents'][0].get('isRoot',False) ^ bool(parent_id):
            return item

    # Create if not existing
    body = {'title':title, 'mimeType':FOLDER_MIME}
    if parent_id:
        body['parents'] = [{'id':parent_id}]
    return service.files().insert(body=body).execute()

def put_file(service, file_path, title, root_collection_id, collection=None, convert=False, description='',
        mime_type='application/octet-stream', overwrite=False):
    sub_colls = (collection.split('/') if collection else [])

    # Check file exists
    if not os.path.exists(file_path):
        raise ValueError('File "%s" not found!' % file_path)

    # Creates or loads collection recursively to support subcollections
    collection_id = root_collection_id
    for coll_title in sub_colls:
        # Check existing collection
        search = service.files().list(q="title='%s' and mimeType='%s' and '%s' in parents" % (
            coll_title, FOLDER_MIME, collection_id)).execute()

        # Create if not existing
        if search['items']:
            collection_id = search['items'][0]['id']
        else:
            info = service.files().insert(body={
                'title': coll_title,
                'mimeType': FOLDER_MIME,
                'parents': [{'id':collection_id}],
                }).execute()
            collection_id = info['id']

    # Verify if file exists
    file_id = None
    if overwrite:
        search = service.files().list(q="title='%s' and mimeType='%s' and '%s' in parents" % (
            title, mime_type, collection_id)).execute()
        if search['items']:
            file_id = search['items'][0]['id']
            info = service.files().delete(fileId=file_id).execute()

    # Save file
    body = {
        'title': title,
        'mimeType': mime_type,
        'convert': bool(convert),
        'parents': [{'id':collection_id}], #, 'kind':'drive#parentReference'}],
        }
    if description:
        body['description'] = description
    media_body = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

    # File upload
    file_info = service.files().insert(body=body, media_body=media_body).execute()

    return file_info

def remove_file(service, file_id):
    info = service.files().delete(fileId=file_id).execute()


class GoogleDrive(BaseEngine):
    def save_file(self, form, obj, doc, attfile):
        dir_path, file_name = os.path.split(form.generate_attachment_filename(obj, attfile.name))

        # Saving in temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(attfile.read())
        temp_file.close()

        # Google Driver API service
        service = form.get_google_drive_service()
        root_collection_id = form.get_google_drive_root_collection_id()

        # Uploading file to Google Drive
        info = put_file(
            service=service,
            file_path=temp_file.name,
            title=file_name,
            root_collection_id=root_collection_id,
            collection=dir_path,
            convert=False,
            mime_type=doc['mime_type'],
            )

        # File info in document
        doc['storage_info'] = {
            'file_id': info['id'],
            'download_url': info.get('downloadUrl',''),
            'thumb_url': info.get('thumbnailLink',''),
            'alternate_url': info.get('alternateLink',''),
            }
        doc.save()

        # Temporary file deletion
        os.unlink(temp_file.name)

    def remove_file(self, form, obj, doc):
        if doc['storage_info'] and doc['storage_info'].get('file_id',None):
            service = form.get_google_drive_service()
            try:
                remove_file(service, doc['storage_info']['file_id'])
            except HttpError as e:
                pass


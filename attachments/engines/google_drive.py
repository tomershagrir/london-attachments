import os
import datetime
import httplib2
import json
import urllib

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import FlowExchangeError
from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build
from apiclient.http import MediaFileUpload

from attachments import app_settings
from base import BaseEngine

FOLDER_MIME = 'application/vnd.google-apps.folder'

def get_flow():
    flow = OAuth2WebServerFlow(
        app_settings.GOOGLE_DRIVE_CLIENT_ID,
        app_settings.GOOGLE_DRIVE_CLIENT_SECRET,
        ' '.join(app_settings.GOOGLE_DRIVE_SCOPES),
        None, # user_agent
        "https://accounts.google.com/o/oauth2/auth",
        "https://accounts.google.com/o/oauth2/token",
        )
    flow.redirect_uri = app_settings.GOOGLE_DRIVE_REDIRECT_URL
    return flow

def get_authorization_url(user_id, state, flow=None):
    if not flow:
        flow = get_flow()

    flow.params['access_type'] = 'offline'
    flow.params['approval_prompt'] = 'force'
    flow.params['user_id'] = user_id
    flow.params['state'] = state
    # u'code': [u'4/rdMBTpmiemBITpy12bTCMHlEOOe6.slmVgVOMScYcshQV0ieZDArYbERicgI']

    return flow.step1_get_authorize_url(app_settings.GOOGLE_DRIVE_REDIRECT_URL)

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

def put_file(service, file_path, title, root_collection_id, collection=None, convert=False, description='', mime_type='application/octet-stream'):
    sub_colls = (collection.split('/') if collection else [])

    # Check file exists
    if not os.path.exists(file_path):
        raise ValueError('File "%s" not found!' % file_path)

    # Creates or loads collection recursively to support subcollections
    collection_id = root_collection_id
    for coll_title in sub_colls:
        # Check existing collection
        search = service.files().list(q="title='%s' and mimeType='%s' and '%s' in parents" % (coll_title, FOLDER_MIME, collection_id)).execute()

        # Create if not existing
        if search['items']:
            collection_id = search['items'][0]['id']
        else:
            info = service.files().insert(body={
                'title':coll_title,
                'mimeType':FOLDER_MIME,
                'parents':[{'id':collection_id}],
                }).execute()
            collection_id = info['id']

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


class GoogleDrive(BaseEngine):
    pass


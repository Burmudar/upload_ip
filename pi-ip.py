from __future__ import print_function
import httplib2
import os
import io
import datetime
import json
import simplejson

from apiclient import http
from apiclient import errors
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from requests import get

SCOPES = 'https://www.googleapis.com/auth/drive.file'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'OAuthTest'
FILE_NAME = 'pi-ip.json'
MIME_TYPE = 'text/plain'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def create_file(service, body):
    try:
        content = http.MediaIoBaseUpload(io.StringIO(body), mimetype=MIME_TYPE, chunksize=-1,resumable=False)
        results = service.files().create(body={'name': FILE_NAME, 'title': 'IP Address', 'description': 'IP Address of PI'}, media_body=content).execute()
    except errors.HttpError as e:
        try:
            # Load Json body.
            error = simplejson.loads(e.content)
            print('Error code: {}'.format(error.get('code')))
            print('Error message: {}'.format(error.get('message')))
            # More error information can be retrieved with error.get('errors').
        except ValueError:
            # Could not load Json body.
            print('HTTP Status code: {}'.format(e.resp.status))
            print('HTTP Reason: {}'.format(e.resp.reason))

def update_file(service, id, body):
    try:
        content = http.MediaIoBaseUpload(io.StringIO(body), mimetype=MIME_TYPE, chunksize=-1,resumable=False)
        results = service.files().update(fileId=id, media_body=content).execute()
    except errors.HttpError as e:
        try:
            # Load Json body.
            print(e.content)
            import pprint
            pprint.pprint(e)
            error = simplejson.loads(e.content)
            print('Error code: {}'.format(error.get('code')))
            print('Error message: {}'.format(error.get('message')))
            # More error information can be retrieved with error.get('errors').
        except ValueError:
            # Could not load Json body.
            print('HTTP Status code: {}'.format(e.resp.status))
            print('HTTP Reason: {}'.format(e.resp.reason))

def find_first_file_id(service, file_name):
    results = service.files().list(q="name = '{}'".format(FILE_NAME), fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        return None
    else:
        return items[0]['id']

def get_external_ip():
    ip = get('https://api.ipify.org').text
    return ip


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'credentials.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    credentials = get_credentials()

    http = httplib2.Http()
    http = credentials.authorize(http)

    service = discovery.build('drive', 'v3', http=http)
    ip = get_external_ip()
    content = json.dumps({'ip': ip, 'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%s")}, indent=4)
    file_id = find_first_file_id(service, FILE_NAME)
    if file_id is None:
        print("No {} file exists. Creating file with content: {}".format(FILE_NAME, content))
        create_file(service, content)
    else:
        print("Updating {} file content: {}".format(FILE_NAME, content))
        update_file(service, file_id, content)

if __name__ == '__main__':
    main()


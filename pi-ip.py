from __future__ import print_function
import httplib2
import os
import io
import datetime
import json

from apiclient import http
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from requests import get

SCOPES = 'https://www.googleapis.com/auth/drive.file'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'OAuthTest'

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def create_file(service, body):
    content = http.MediaIoBaseUpload(io.StringIO(body), mimetype="text/plain", chunksize=-1,resumable=False)
    results = service.files().create(body={'name': 'pi-ip.txt', 'title': 'IP Address', 'description': 'IP Address of PI'}, media_body=content).execute()
    import pprint
    pprint.pprint(results)

def update_file(service, id, body):
    content = http.MediaIoBaseUpload(io.StringIO(body), mimetype="text/plain", chunksize=-1,resumable=False)
    results = service.files().update(fileId=id, media_body=content).execute()
    import pprint
    pprint.pprint(results)

def find_first_file_id(service, file_name):
    results = service.files().list(q="name = 'pi-ip.txt'", fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        return -1
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
    file_id = find_first_file_id(service, "pi-ip.txt")
    if file_id is None:
        print("pi-ip.txt file not found! Creating it")
        create_file(service, content)
    else:
        print("pi-ip file found! Updating with content: {0}".format(content))
        update_file(service, file_id, content)

if __name__ == '__main__':
    main()



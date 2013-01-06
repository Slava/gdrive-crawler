#! /usr/env python
from optparse import OptionParser
import requests
import urllib
import json
import os

ELASTIC_SEARCH = 'http://' + os.getenv('BONSAI_URL', 'localhost:9200')

parser = OptionParser()
parser.add_option('-u', '--username', dest='username',
                  help='full email, ex.: slava@collections.me')
parser.add_option('-a', '--access_token', dest='access_token',
                  help='access token from gdrive API')

(options, args) = parser.parse_args()

username = options.username.strip()
access_token = options.access_token.strip()

if not username:
    raise Exception('username can not be None')
if not access_token:
    raise Exception('access_token can not be None')

page_token = None

while True:
    try:
        params = {}
        headers = {}

        headers['Authorization'] = 'Bearer ' + access_token

        if page_token:
            params['pageToken'] = page_token

        request = requests.get('https://www.googleapis.com/drive/v2/files',
                               params=params, headers=headers, timeout=10)
        response = request.json()

        for item in response['items']:
            jsoned_data = json.dumps(item)
            put_url = ELASTIC_SEARCH + '/' + urllib.quote(username) + \
                        '/gdrive_item/' + urllib.quote(item['id'])
            index_request = requests.put(put_url, data=jsoned_data, timeout=10)
            print index_request

    except Exception as e:
        import traceback
        print 'shii..~~'
        traceback.print_exc()

    if not page_token:
        break

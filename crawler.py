#! /usr/env python
from optparse import OptionParser
from urlparse import urlparse
import requests
import urllib
import json
import os

ELASTIC_SEARCH = str(os.getenv('BONSAI_URL', 'http://localhost:9200'))

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
            index_item = {}
            important_fields = ['title', 'alternateLink', 'mimeType',
                                'ownerNames', 'id', 'createdDate',
                                'modifiedDate']

            for field in important_fields:
                if field in item:
                    index_item[field] = item[field]

            index_item['account'] = username

            try:
                contents_link = item['exportLinks']['text/plain']
                index_item['content'] = requests.get(contents_link).text
            except KeyError:
                print 'no plain text contents'
            except Exception:
                print 'other exception while looking for plain text contents'

            jsoned_data = json.dumps(index_item)

            put_url = ELASTIC_SEARCH + '/all_documents' + \
                '/gdrive_item/' + urllib.quote(item['id'])
            parsed_url = urlparse(ELASTIC_SEARCH)

            index_request = requests.put(put_url, data=jsoned_data, timeout=10,
                                         auth=(parsed_url.username,
                                               parsed_url.password))
            print 'index', item['id'], index_request,\
                  put_url, parsed_url.username, parsed_url.password

    except Exception as e:
        import traceback
        print 'shii..~~'
        traceback.print_exc()

    if not page_token:
        break

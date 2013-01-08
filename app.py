import tornado.ioloop
import tornado.web
import tornado.options
import subprocess
import logging
import requests
import os
import urllib

from tornado import template
from pyjade.ext.tornado import patch_tornado
from urlparse import urlparse

patch_tornado()
template_loader = template.Loader('./public/jade')

ELASTIC_SEARCH = str(os.getenv('BONSAI_URL', 'http://localhost:9200'))


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(template_loader.load('index.jade').generate())


class SearchHandler(tornado.web.RequestHandler):
    def _get_auth(self, url):
        parsed_url = urlparse(url)
        return (parsed_url.username, parsed_url.password)

    def _beautify_response(self, response):
        result = []

        for hit in response['hits']['hits']:
            item = hit['_source']

            result.append({
                'title': item['title'],
                'id': item['id'],
                'account': item['account'],
                'link': item.get('alternateLink', 'http://bit.ly/ScQadK')
            })

        return result

    def search(self, query):
        request = requests.get(ELASTIC_SEARCH + '/all_documents/_search',
                               params={'q': 'title:' + query},
                               auth=self._get_auth(ELASTIC_SEARCH))
        response = request.json()
        return self._beautify_response(response)

    def search_content(self, query):
        request = requests.get(ELASTIC_SEARCH + '/all_documents/_search',
                               params={'q': 'content:' + query},
                               auth=self._get_auth(ELASTIC_SEARCH))
        response = request.json()
        return self._beautify_response(response)

    def get(self):
        query = urllib.unquote(self.get_argument('query', default=''))
        self.write(template_loader.load('search_results.jade')
            .generate(query=query,
                      items=self.search(query),
                      items_cont=self.search_content(query),
                      fields=['title', 'account', 'link', 'id']))


class AddHandler(tornado.web.RequestHandler):
    def get(self):
        username = self.get_argument('username', default=None)
        access_token = self.get_argument('access_token', default=None)

        if username is None or access_token is None:
            raise tornado.web.HTTPError(400)

        subprocess.Popen(['python', 'crawler.py',
                         '-u', urllib.unquote(username),
                         '-a', urllib.unquote(access_token)])
        self.write(template_loader.load('success.jade').generate())
        logging.info('crawling of ' + username + ' with AT '
                     + access_token + ' started')

app = tornado.web.Application([
    (r'/', RootHandler),
    (r'/search', SearchHandler),
    (r'/add', AddHandler),
    (r'/css/(.*)', tornado.web.StaticFileHandler, {'path': './public/css/'})
])

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app.listen(os.getenv('PORT', 8888))
    tornado.ioloop.IOLoop.instance().start()

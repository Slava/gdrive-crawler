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

patch_tornado()
template_loader = template.Loader('./public/jade')

ELASTIC_SEARCH = os.getenv('BONSAI_URL', 'http://localhost:9200/')


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(template_loader.load('index.jade').generate())


class SearchHandler(tornado.web.RequestHandler):
    def search(self, query):
        request = requests.get(ELASTIC_SEARCH + '_search',
                               params={'q': 'title:' + query})
        response = request.json()
        result = []

        for hit in response['hits']['hits']:
            item = hit['_source']

            result.append({
                'title': item['title'],
                'thumbnail': item.get('thumbnailLink', 'http://bit.ly/ScQadK')
            })

        return result

    def get(self):
        query = urllib.unquote(self.get_argument('query', default=''))
        self.write(template_loader.load('search_results.jade')
            .generate(query=query,
                      items=self.search(query),
                      fields=['title', 'thumbnail']))


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

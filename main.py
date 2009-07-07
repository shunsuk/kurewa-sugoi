# -*- coding: utf-8 -*-

import cgi
import os
import re
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class GlobalIndex(db.Model):
  max_index = db.IntegerProperty(required=True, default=1)

class Bookmark(db.Model):
  id = db.IntegerProperty()
  username = db.StringProperty()
  title = db.StringProperty(multiline=True)
  url = db.StringProperty()
  count = db.StringProperty()
  comment = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
  def get(self):
    bookmarks_query = Bookmark.all().order('-id')
    bookmarks = bookmarks_query.fetch(30)

    latest_id = 0
    if len(bookmarks) > 0:
      latest_id = bookmarks[0].id

    template_values = {
      'bookmarks': bookmarks,
      'latest_id': latest_id,
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))

class Hook(webapp.RequestHandler):
  def post(self):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug('username(hook)=' + self.request.get('username'))

    if (self.request.get('status') == 'add' or self.request.get('status') == 'update') and \
        self.request.get('is_private') == '0' and \
        self.request.get('comment').find(unicode('[これはすごい]', 'utf_8')) != -1:
      logging.debug('username(sugoi)=' + self.request.get('username'))

      create_bookmark(self.request.get('username'),
                  self.request.get('title'),
                  self.request.get('url'),
                  self.request.get('count'),
                  self.request.get('comment'))
    #self.redirect('/')

def create_bookmark(username, title, url, count, comment):
  def txn():
    bookmark_index = GlobalIndex.get_by_key_name('Bookmark')
    if bookmark_index is None:
      bookmark_index = GlobalIndex(key_name='Bookmark')
    new_id = bookmark_index.max_index
    bookmark_index.max_index += 1
    bookmark_index.put()

    b = Bookmark(key_name='Bookmark' + str(new_id), parent=bookmark_index)
    b.id = new_id
    b.username = username
    b.title = title
    b.url = url
    b.count = count
    b.comment = comment
    b.put()
  db.run_in_transaction(txn)

class Diff(webapp.RequestHandler):
  def get(self):
    latest_id = int(self.request.get('latest_id'))
    bookmarks_query = Bookmark.all().filter('id >', latest_id).order('id')
    bookmarks = bookmarks_query.fetch(1)
    if len(bookmarks) > 0:
      json = '{latest_id:' + str(bookmarks[len(bookmarks) - 1].id) + ',bookmark:'
      b = bookmarks[0]
      json += '{'
      json += 'id:"' + str(b.id) + '",'
      json += 'url:"' + b.url + '",'
      json += 'title:"' + re.sub('\n', '', b.title) + '",'
      json += 'username:"' + b.username + '",'
      json += 'comment:"' + b.comment + '"},'
      json = json[0 : len(json) - 1]
      json += '}'
      self.response.out.write(json)
    else:
      self.response.out.write('{latest_id:' + str(latest_id) + '}')

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/hook', Hook),
                                      ('/diff', Diff)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Mike Wild'
SITENAME = u'Mike Wild'
SITEURL = 'https://mikeanthonywild.com' # Only valid for local dev
THEME = u'theme'
FOOTERTEXT = u'Content and design by \
<a href="https://twitter.com/mikeanthonywild">{}</a>'.format(AUTHOR)

PATH = 'content'
STATIC_PATHS = ['images', 'extra/keybase.txt']
EXTRA_PATH_METADATA = {'extra/keybase.txt': {'path': 'keybase.txt'}}

TIMEZONE = 'Europe/London'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 5

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# -*- coding: utf-8 -*-
try:
    from djangoappengine.settings_base import *
    has_djangoappengine = True
except ImportError:
    has_djangoappengine = False
    DEBUG = True
    TEMPLATE_DEBUG = DEBUG

import os

# Uncomment the following if you want to use MongoDB
# -----------------
#DATABASES = {
#    'default': {
#        'ENGINE': 'django_mongodb_engine.mongodb',
#        'NAME': 'test',
#        'USER': '',
#        'PASSWORD': '',
#        'HOST': 'localhost',
#        'PORT': 27017,
#        'SUPPORTS_TRANSACTIONS': False,
#    }
#}
# -----------------

SITE_NAME = 'SynBioWorld'
SITE_DESCRIPTION = ''
SITE_COPYRIGHT = ''
DISQUS_SHORTNAME = 'synbioworld'
GOOGLE_ANALYTICS_ID = 'UA-20401429-1'
# Get the ID from the CSE "Basics" control panel ("Search engine unique ID")
GOOGLE_CUSTOM_SEARCH_ID = '010791766044768696767:y6gd7ny6thy'
# Set RT username for retweet buttons
TWITTER_USERNAME = 'synbioworld'
# In order to always have uniform URLs in retweets and FeedBurner we redirect
# any access to URLs that are not in ALLOWED_DOMAINS to the first allowed
# domain. You can have additional domains for testing.
ALLOWED_DOMAINS = ()

SECRET_KEY = '=r-$b*8hglm+858&9t043hlm6-&6-3d3vfc4((7yd0dbrakhvi'

SITE_ID = 34

ACCOUNT_ACTIVATION_DAYS = 7
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'dbikard@gmail.com'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'minicms',
    'blog',
    'disqus',
    'djangotoolbox',
    'mediagenerator',
    'simplesocial',
    'librarian',
    'registration',
    'chatroom',
    'jobs',
)

if has_djangoappengine:
    # djangoappengine should come last, so it can override a few manage.py commands
    INSTALLED_APPS += ('djangoappengine',)

TEST_RUNNER = 'djangotoolbox.test.CapturingTestSuiteRunner'

REST_BACKENDS = (
    'minicms.markup_highlight',
    'blog.markup_posts',
    'blog.feed',
)

MIDDLEWARE_CLASSES = (
    'mediagenerator.middleware.MediaMiddleware',
    'django.middleware.common.CommonMiddleware',
    'djangotoolbox.middleware.RedirectMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'minicms.middleware.CMSFallbackMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.media',
    'minicms.context_processors.cms',
)

USE_I18N = False

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

MEDIA_BUNDLES = (
    ('main.css',
        'design.sass',
        'rest.css',
        'project-feed.css',
        'search-design.css',
    ),
    ('mainjs.js',
         'jquery.js',
         'channel_chat.js',
	 'jquery.poll.js',
    ),
)

ROOT_MEDIA_FILTERS = {
    'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
    'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
}

YUICOMPRESSOR_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                  'yuicompressor.jar')

MEDIA_DEV_MODE = DEBUG
DEV_MEDIA_URL = '/devmedia/'
PRODUCTION_MEDIA_URL = '/media/'

GLOBAL_MEDIA_DIRS = (
    os.path.join(os.path.dirname(__file__), 'static'),
)

ADMIN_MEDIA_PREFIX = '/media/admin/'

ROOT_URLCONF = 'urls'

NON_REDIRECTED_PATHS = ('/admin/',)

# Activate django-dbindexer if available
try:
    import dbindexer
    DATABASES['native'] = DATABASES['default']
    DATABASES['default'] = {'ENGINE': 'dbindexer', 'TARGET': 'native'}
    INSTALLED_APPS += ('dbindexer',)
    MIDDLEWARE_CLASSES = ('dbindexer.middleware.DBIndexerMiddleware',) + \
                         MIDDLEWARE_CLASSES
except ImportError:
    pass

try:
    from settings_local import *
except ImportError:
    pass

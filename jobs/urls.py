from django.conf.urls.defaults import *


urlpatterns = patterns('jobs.views',
    (r'^$','jobsRSS'),
)

from django.conf.urls.defaults import *


urlpatterns = patterns('chatroom.views',
    (r'^$','chatroom'),
    (r'^post_msg/$', 'Receive'),
    (r'^get_token/$', 'GetToken'),
    (r'^open/$', 'Open'),
)

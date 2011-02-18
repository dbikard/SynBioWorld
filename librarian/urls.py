from django.conf.urls.defaults import *


urlpatterns = patterns('librarian.views',
    (r'^$', 'librarian_home'),
    (r'^paper/(?P<list_type>\w+)/$', 'list_paper'),
    (r'^paper/show/(?P<paper_id>\d+)/$', 'show_paper'),
    (r'^person/$', 'list_people'),
    (r'^person/show/(?P<person_id>\d+)/$', 'show_person'),
    (r'^institution/$', 'list_institution'),
    (r'^institution/show/(?P<key>\d+)$', 'show_institution'),
    (r'^country/$', 'list_country'),
    (r'^country/show/(?P<key>\d+)$', 'show_country'),
    (r'^journal/$', 'list_journal'),
    (r'^journal/show/(?P<key>\d+)$', 'show_journal'),
    (r'^add/$', 'add_papers'),
    (r'^import_ISI_data/$', 'import_ISI_data'),
    (r'^update_SBW/$', 'update_SBW_view'),
    #~ (r'^search/$', 'search'),
)

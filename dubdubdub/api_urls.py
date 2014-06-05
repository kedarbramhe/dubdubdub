from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page

from schools.api_views import SchoolsList, SchoolsInfo, SchoolInfo, Districts, \
    SchoolsDiseInfo, SchoolDemographics, SchoolProgrammes, SchoolFinance, \
    Blocks, Clusters

urlpatterns = patterns('',
    # Caches the results of the url for 60 seconds
    url(r'^schools/list', cache_page(60)(SchoolsList.as_view()), name='api_schools_list'),
    url(r'^$', 'schools.api_views.api_root', name='api_root'),
    url(r'^schools/list', SchoolsList.as_view(), name='api_schools_list'),
    url(r'^schools/info', SchoolsInfo.as_view(), name='api_schools_info'),
    url(r'^schools/dise/(?P<year>[0-9\-]*)$', SchoolsDiseInfo.as_view(), name='api_schools_dise'),

    url(r'^schools/school/(?P<pk>[0-9]+)$', SchoolInfo.as_view(), name='api_school_info'),
    url(r'^schools/school/(?P<pk>[0-9]+)/demographics$', SchoolDemographics.as_view(), name='api_school_demo'),
    url(r'^schools/school/(?P<pk>[0-9]+)/programmes$', SchoolProgrammes.as_view(), name='api_school_prog'),
    url(r'^schools/school/(?P<pk>[0-9]+)/finance$', SchoolFinance.as_view(), name='api_school_finance'),
    
    url(r'^boundary/districts$', Districts.as_view(), name="api_districts"),
    url(r'^boundary/blocks$', Blocks.as_view(), name="api_blocks"),
    url(r'^boundary/clusters$', Clusters.as_view(), name="api_clusters"),
)

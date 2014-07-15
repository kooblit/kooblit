from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^login/$', 'usr_management.views.contact', name='login'),
    url(r'^logout$', 'usr_management.views.user_logout', name='logout'),
    url(r'^delete$', 'usr_management.views.user_suppression', name='delete'),
    url(r'^confirmation/(?P<verification_id>[0-9a-f]{64})$', 'usr_management.views.email_confirm', name='email_confirm'),
    url(r'^InputValidator', 'usr_management.views.check_exist', name='validator'),
)
from django.conf.urls.defaults import patterns

urlpatterns = patterns('celex.views',
    (r'^$','index'),
    (r'^reset/$','reset'),
    #(r'^Kevin/$','Kevin'),
)

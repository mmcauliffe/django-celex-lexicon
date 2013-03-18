from django.conf.urls.defaults import patterns

urlpatterns = patterns('celex.views',
    (r'^$','index'),
    (r'^reset/$','reset'),
    (r'^stringselect/$','string_selection'),
    (r'^analyze/$','analyze_ngrams'),
    #(r'^Kevin/$','Kevin'),
)

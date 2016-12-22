from django.contrib import admin

try:
    from django.conf.urls import patterns, include

    urlpatterns = patterns(
        '',
        (r'^admin/', include(admin.site.urls)),
    )
except ImportError:
    # Django >= 1.10
    from django.conf.urls import url, include

    urlpatterns = [
        url(r'^admin/', include(admin.site.urls)),
    ]

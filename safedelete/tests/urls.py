from django.contrib import admin

try:
    from django.conf.urls import include, patterns

    urlpatterns = patterns(
        '',
        (r'^admin/', include(admin.site.urls)),
    )
except ImportError:
    try:
        # Django >= 2.0
        from django.urls import path

        urlpatterns = [
            path('admin/', admin.site.urls),
        ]
    except ImportError:
        # Django >= 1.10
        from django.conf.urls import include, url

        urlpatterns = [
            url(r'^admin/', include(admin.site.urls)),
        ]

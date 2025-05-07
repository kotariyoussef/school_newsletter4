from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import ProfileListView, ProfileDetailView
from news.views import NewsList
from news.sitemap import NewsSitemap
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.cache import cache_page
from .robots import robots_txt

from django.urls import path

# Custom error handler
handler404 = 'subscription.views.error_404_view'
handler500 = 'subscription.views.error_500_view'
handler403 = 'subscription.views.error_403_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('news/', include('news.urls')),
    path('', include("subscription.urls")),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('profiles/', ProfileListView.as_view(), name='profile_list'),
    path('', NewsList.as_view(), name='home'),
    path("sitemap.xml", 
            cache_page(86400)(sitemap),
            {"sitemaps": {"news": NewsSitemap}},
            name="django.contrib.sitemaps.views.sitemap"
         ),
    path("robots.txt", robots_txt, name="robots_txt"),
    path('<slug:slug>/', ProfileDetailView.as_view(), name='profile_detail'),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


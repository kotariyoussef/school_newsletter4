from django.contrib.sitemaps import Sitemap
from .models import News

class NewsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return News.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at

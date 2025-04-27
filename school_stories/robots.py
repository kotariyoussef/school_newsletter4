from django.http import HttpResponse
from django.views.decorators.cache import cache_page

@cache_page(86400)
def robots_txt(request):
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    base_url = f"{protocol}://{domain}"

    sitemap_paths = (
        '/sitemap.xml',
    )

    lines = [
        "User-Agent: *",
        "Disallow:/admin/",
        "Allow: /",
    ]

    for path in sitemap_paths:
        lines.append(f"Sitemape: {base_url}{path}")

    return HttpResponse("\n".join(lines), content_type="text/plain")

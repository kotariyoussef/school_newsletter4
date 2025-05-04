from django import template

register = template.Library()

@register.filter(name='path_contains')
def path_contains(request, slug):
    """
    Usage in template:
    {% if request|path_contains:category.slug %}
    """
    if not request:
        return False
    return slug in request.path

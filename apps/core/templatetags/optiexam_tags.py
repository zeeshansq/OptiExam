from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.simple_tag
def icon(name: str, css_class: str = "icon", **kwargs):
    """
    Renders an inline SVG referencing local Lucide icon sprite.
    Usage: {% icon 'shield' 'icon-lg' %}
    """
    classes = set(css_class.split())
    classes.add("icon")
    final_class = ' '.join(sorted(classes))
    extra_attrs = ' '.join(f'{k}="{v}"' for k, v in kwargs.items())
    html = f'''<svg class="{final_class}" aria-hidden="true" {extra_attrs}>
      <use href="/static/icons/lucide-sprite.svg#{name}"></use>
    </svg>'''
    return mark_safe(html)

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Preserves existing GET query parameters while updating/adding new ones.
    Usage: <a href="?{% query_transform page=2 %}">2</a>
    """
    request = context.get('request')
    if not request:
        return ""
    updated = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None and v != "":
            updated[k] = v
        else:
            updated.pop(k, None)
    return updated.urlencode()

@register.simple_tag(takes_context=True)
def sort_header(context, field_name: str, label: str):
    """
    Renders a clickable table header with sorting indicator (↑ / ↓ / ↕).
    Usage: {% sort_header 'name' 'Institution Name' %}
    """
    request = context.get('request')
    current_sort = request.GET.get('sort', '') if request else ''
    current_order = request.GET.get('order', 'asc') if request else 'asc'

    is_active = (current_sort == field_name)
    next_order = 'desc' if (is_active and current_order == 'asc') else 'asc'
    
    updated = request.GET.copy() if request else {}
    updated['sort'] = field_name
    updated['order'] = next_order
    # Reset page on new sort
    updated['page'] = '1'
    url = f"?{updated.urlencode()}" if hasattr(updated, 'urlencode') else f"?sort={field_name}&order={next_order}"

    if is_active:
        indicator = "↑" if current_order == "asc" else "↓"
        active_class = "sort-active"
    else:
        indicator = "↕"
        active_class = ""

    html = f'''<a href="{url}" class="table-sort-header {active_class}" title="Sort by {escape(label)}">
      <span>{escape(label)}</span>
      <span class="sort-indicator">{indicator}</span>
    </a>'''
    return mark_safe(html)

@register.filter
def get_item(dictionary, key):
    """
    Template filter to look up a key in a dictionary or object.
    Usage: {{ dict|get_item:key }}
    Handles string and integer keys smoothly.
    """
    if not isinstance(dictionary, dict):
        return ""
    
    # Try exact key, string key, or int key
    if key in dictionary:
        return dictionary[key]
    str_key = str(key)
    if str_key in dictionary:
        return dictionary[str_key]
    try:
        int_key = int(key)
        if int_key in dictionary:
            return dictionary[int_key]
    except (ValueError, TypeError):
        pass
    return ""


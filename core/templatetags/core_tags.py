"""Custom template tags used across the entire phenotype_inventory project."""

from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.simple_tag(takes_context=True)
def render_as_template(context, template_as_string):
    """Renders a template variable as template code.
    
    Source:
        https://github.com/daniboy/django-render-as-template
        Taken from render_as_template.templatetags.render_as_template
    """
    template_as_object = context.template.engine.from_string(template_as_string)
    return template_as_object.render(context)


@register.filter(name='has_group')
def has_group(user, group_name):
    """Tests if a user belongs to a given group.
    
    Source:
        https://www.abidibo.net/blog/2014/05/22/check-if-user-belongs-group-django-templates/#sthash.vGVYYdzi.dpuf
    """
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False

"""Custom template tags used across the entire phenotype_inventory project."""

from django import template

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
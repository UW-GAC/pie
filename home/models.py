from django.db            import models
from ordered_model.models import OrderedModel

class HomeContent(OrderedModel):
    '''
    Model to handle content to display on the home page.
    '''
    title          = models.CharField(max_length=250)
    content        = models.TextField()
    web_date_added = models.DateTimeField(auto_now_add=True, auto_now=False)

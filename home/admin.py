from django.contrib      import admin
from .models             import HomeContent
from ordered_model.admin import OrderedModelAdmin

class HomeContentAdmin(OrderedModelAdmin):
    '''
    '''
    list_display = ('title', 'web_date_added', 'order', 'move_up_down_links', )
    list_filter = ('web_date_added', )
    search_fields = ('title', )

admin.site.register(HomeContent, HomeContentAdmin)
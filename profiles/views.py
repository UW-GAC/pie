from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .tables import *
from .models import *


@login_required
def profile(request):
    # user is automatically passed in the request somehow
    page_title = 'profile'

    if request.method == "POST":
        # remove saved searches
        if 'search_type' in request.POST:
            search_removal_list = request.POST.getlist('search_id')
            for search_id in search_removal_list:
                saved_search = SavedSearchMeta.objects.get(search_id=search_id)
                saved_search.active = False
                saved_search.save()

    savedsource = SourceSearchTable(build_usersearches(request.user.id, 'source'), request=request)
    savedharmonized = HarmonizedSearchTable(build_usersearches(request.user.id, 'harmonized'), request=request)

    # RequestConfig(request).configure(savedsource)
    # RequestConfig(request).configure(savedharmonized)


    return render(
        request,
        'profiles/profile.html',
        {'page_title': page_title, 'savedsource': savedsource, 'savedharmonized': savedharmonized}
    )


def build_usersearches(user_id, search_type):
    """Return a list of dictionaries for building user's saved searches"""
    searches = Search.objects.select_related().filter(
        userdata__user_id=user_id,
        search_type=search_type,
        savedsearchmeta__active=True)
    data = [
        {
            'search_id': x.id,
            'search_text': x.param_text,
            # only used in SourceSearchTable
            'search_studies': len([y['i_study_name'] for y in x.param_studies.values()]),
            'study_name_string': '<br>'.join([y['i_study_name'] for y in x.param_studies.values()]),
            'search_url': x.build_search_url(),
            'date_saved': x.created
        }
        for x in searches
    ]
    return data

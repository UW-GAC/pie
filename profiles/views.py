from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from profiles.models import Search
from .tables import SourceSearchTable, HarmonizedSearchTable

from django_tables2 import RequestConfig

# Create your views here.

@login_required
def profile(request):
    # user is automatically passed in the request somehow
    page_title = 'profile'

    savedsource = SourceSearchTable(build_usersearches(request.user.id, 'source'),request=request)
    savedharmonized = HarmonizedSearchTable(build_usersearches(request.user.id, 'harmonized'), request=request)

    # RequestConfig(request).configure(savedsource)
    # RequestConfig(request).configure(savedharmonized)

    return render(request, 'profiles/profile.html',
        {'page_title': page_title, 'savedsource': savedsource, 'savedharmonized': savedharmonized}
    )

def build_usersearches(user_id, search_type):
    """Return a list of dictionaries for building user's saved searches"""
    searches = Search.objects.select_related().filter(userdata__user_id=user_id, search_type=search_type)
    data = [
        {
            'search_id': x.id,
            'search_text': x.param_text,
            # only used in SourceSearchTable
            'search_studies': len([y['i_study_name'] for y in x.param_studies.values()]),
            'study_name_string': '\n'.join([y['i_study_name'] for y in x.param_studies.values()]),
            'search_url': Search.build_search_url(
                search_type, x.param_text, [s[0] for s in x.param_studies.values_list('i_accession')]
            )
        }
        for x in searches
    ]
    return data

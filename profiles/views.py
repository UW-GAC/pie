from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def profile(request):
    # user is automatically passed in the request somehow
    page_title = 'profile'
    return render(request, 'profiles/profile.html',
        {'page_title': page_title}
    )


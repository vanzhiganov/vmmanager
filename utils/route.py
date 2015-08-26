import re
from django.http import HttpResponse, Http404

def dispatch_url(urlmap, url, request):
    for p in urlmap.keys():
        foo_url = re.sub(p, "", url)
        if url != foo_url:
            obj = urlmap[p]
            url = foo_url
            return obj().root(request, url)
    raise Http404
from django.views.generic import View
from django.contrib.gis.geos import Polygon
#from coords.models import InstCoord
from .models import School, InstCoord
from common.views import APIView
from django.core.paginator import Paginator

ITEMS_PER_PAGE = 50 #move this to settings if it is a constant?

class SchoolsList(APIView):

    def get(self, *args, **kwargs):
        bbox_string = self.request.GET.get("bounds")
        page = int(self.request.GET.get("page", 1))
        #TODO: refactor to accept CSV as param
        if bbox_string:
            schools = School.objects.within_bbox(bbox_string)
        else:
            schools = School.objects.all()
        schools = schools.select_related('instcoord', 'address')
        p = Paginator(schools, ITEMS_PER_PAGE)
        page = p.page(page)

        context = {
            'type': 'FeatureCollection',
            'count': p.count,
            'features': [s.get_list_geojson() for s in page.object_list]
        }

        # we can return custom HTTP Status code like this
        return self.render_to_response(context, status=200)


class SchoolsInfo(APIView):

    def get(self, *args, **kwargs):
        bbox_string = self.request.GET.get("bounds")
        page = int(self.request.GET.get("page", 1))
        #TODO: refactor to accept CSV as param

        schools = School.objects.all()
        if bbox_string:
            schools = School.objects.within_bbox(bbox_string)
        else:
            schools = School.objects.all()

        schools = schools.select_related('instcoord', 'address')

        p = Paginator(schools, ITEMS_PER_PAGE)
        page = p.page(page)

        context = {
            'type': 'FeatureCollection',
            'count': p.count,
            'features': [s.get_info_geojson() for s in page.object_list]
        }

        # we can return custom HTTP Status code like this
        return self.render_to_response(context, status=200)
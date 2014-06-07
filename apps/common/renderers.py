from rest_framework.renderers import JSONRenderer
from rest_framework_csv.renderers import CSVRenderer

class KLPJSONRenderer(JSONRenderer):
    '''
        Sub-classes JSONRenderer to render GeoJSON where appropriate.
        If the request contains a geometry=yes parameter, it converts features
        to GeoJSON
    '''

    media_type = 'application/json'
    format = 'json'

    def render(self, data, media_type=None, renderer_context=None):

        #figure out whether we need to render geometry based on GET param
        render_geometry = renderer_context['request'].GET.get('geometry', 'no')
        if render_geometry == 'yes':
            self.render_geometry = True
        else:
            self.render_geometry = False

        #if data is a list, that means pagination was turned off with per_page=0
        #then we first need to convert the list to a dict so that we have same data structure:
        if isinstance(data, list):
            data = {
                'features': data
            }

        #if geometry=yes and results are a list, convert to geojson
        if self.render_geometry and data.has_key('features') and isinstance(data['features'], list):
            data['type'] = 'FeatureCollection'
            features = data.pop('features')
            data['features'] = [self.get_feature(elem) for elem in features]
 
        #if geometry=yes and is a single feature, convert data to geojson
        elif self.render_geometry:
            data = self.get_feature(data)

        #if geometry=no, just convert data as is to JSON
        else:
            pass

        return super(KLPJSONRenderer, self).render(data, media_type, renderer_context)

    def get_feature(self, elem):
        '''
            Passed an element with properties, including a 'geometry' property,
            will convert it to GeoJSON format
        '''
        #this should never be called if geometry=no
        if 'geometry' not in elem:
            raise Exception("Element does not contain a 'geometry' key even though geometry=yes was passed")
        #convert flat dict representation to geojson for the feature
        geometry = elem.pop('geometry')
        feature = {
            'type': 'Feature',
            'geometry': geometry,
            'properties': elem
        }
        return feature


class KLPCSVRenderer(CSVRenderer):
    pass

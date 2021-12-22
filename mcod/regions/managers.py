from decimal import Decimal
from django.db import models
from django.apps import apps

from mcod.regions.api import PeliasApi


class RegionManager(models.Manager):

    def create_new_regions(self, to_create_regions):
        pelias = PeliasApi()
        region = apps.get_model('regions', 'region')
        wof_ids = ['whosonfirst:{}:{}'.format(reg_data['placetype'], reg_id) for
                   reg_id, reg_data in to_create_regions.items()]
        places_details = pelias.place(wof_ids)
        geonames_ids = {feat['properties']['id']: feat['properties']['addendum']['concordances']['gn:id']
                        for feat in places_details.get('features', [])
                        if feat['properties'].get('addendum') and
                        feat['properties']['addendum']['concordances'].get('gn:id')}
        to_create_regions_obj = []
        for reg_id, reg_data in to_create_regions.items():
            _bbox = reg_data['geom']['bbox'].split(',')
            # If both bbox coordinates are the same points, ES throws 'malformed shape error',
            # so we 'enlarge' the shape a little bit.
            if _bbox[0] == _bbox[2] and _bbox[1] == _bbox[3]:
                coords = [Decimal(_bbox[2]), Decimal(_bbox[3])]
                edited_coords = [coord + Decimal('0.000000001') for coord in coords]
                _bbox[2] = str(edited_coords[0])
                _bbox[3] = str(edited_coords[1])
            region_props = dict(
                region_id=reg_id,
                region_type=reg_data['placetype'],
                name_pl=reg_data['names']['pol'][0] if
                reg_data['names'].get('pol') else reg_data['name'],
                name_en=reg_data['names']['eng'][0] if
                reg_data['names'].get('eng') else reg_data['name'],
                hierarchy_label_pl=reg_data['hierarchy_label_pl'],
                hierarchy_label_en=reg_data['hierarchy_label_en'],
                bbox=_bbox,
                lat=reg_data['geom']['lat'],
                lng=reg_data['geom']['lon']
            )
            gn_id = geonames_ids.get(str(reg_id))
            if gn_id:
                region_props['geonames_id'] = gn_id
            to_create_regions_obj.append(region(**region_props))
        created_regions = self.bulk_create(to_create_regions_obj)
        return created_regions

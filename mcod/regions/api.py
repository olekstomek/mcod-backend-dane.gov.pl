import logging

import requests
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from requests.auth import HTTPBasicAuth

from mcod.regions.exceptions import MalformedTerytCodeError

logger = logging.getLogger('mcod')


class BaseApi:
    def __init__(self, url):
        self.url = url
        self.user = settings.GEOCODER_USER
        self.password = settings.GEOCODER_PASS
        self.hierarchy_region_labels = ['locality_id', 'localadmin_id', 'county_id', 'region_id']

    def _send_request(self, api_path, params, err_resp=None):
        url = f"{self.url}{api_path}"
        try:
            resp = requests.get(url, params=params, auth=HTTPBasicAuth(self.user, self.password)).json()
        except requests.exceptions.RequestException as err:
            resp = err_resp if err_resp is not None else []
            logger.error('Error occurred while sending request by {} to url {} with params {} : {}'.format(
                self.__class__.__name__, url, params, err
            ))
        return resp

    def add_hierarchy_labels(self, reg_data):
        return reg_data


class PlaceholderApi(BaseApi):
    def __init__(self):
        super().__init__(settings.PLACEHOLDER_URL)

    def find_by_id(self, ids):
        params = {'ids': ','.join([str(i) for i in ids])}
        resp = self._send_request('/parser/findbyid', params, err_resp={})
        return resp

    def get_all_regions_details(self, ids):
        additional_regions_ids = []
        main_regions_ids = []
        reg_data = self.find_by_id(ids)
        for region in reg_data.values():
            main_regions_ids.append(region['id'])
            place_label = f'{region["placetype"]}_id'
            parent_regions = region['lineage'][0]
            additional_regions_ids.extend(
                [parent_regions[r_type] for r_type in self.hierarchy_region_labels if
                 parent_regions.get(r_type) and r_type != place_label])
        additional_regions_ids = list(frozenset(additional_regions_ids))
        additional_regions_details = self.find_by_id(additional_regions_ids)
        reg_data.update(additional_regions_details)
        self.add_hierarchy_labels(reg_data)
        all_regions_ids = main_regions_ids + additional_regions_ids
        return reg_data, all_regions_ids

    def add_hierarchy_labels(self, reg_data):
        for reg_id, reg_details in reg_data.items():
            parent_regions = reg_details['lineage'][0]
            pl_labels = []
            en_labels = []
            for r_type in self.hierarchy_region_labels:
                parent_id = parent_regions.get(r_type)
                if parent_id:
                    parent_id = str(parent_id)
                    name_pl = reg_data[parent_id]['names']['pol'][0] if\
                        reg_data[parent_id]['names'].get('pol') else reg_data[parent_id]['name']
                    name_en = reg_data[parent_id]['names']['eng'][0] if\
                        reg_data[parent_id]['names'].get('eng') else reg_data[parent_id]['name']
                    if r_type == 'localadmin_id':
                        if not name_pl.startswith('Gmina'):
                            name_pl = f'Gmina {name_pl}'
                        if name_en.startswith('Gmina'):
                            split_name = name_en.split()
                            name_en = f'COMM. {split_name[0]}'
                        else:
                            name_en = f' COMM.{name_en}'
                    elif r_type == 'county_id':
                        name_pl = f'pow. {name_pl}'
                        name_en = f'COU. {name_en}'
                    elif r_type == 'region_id':
                        name_pl = f'woj. {name_pl}'
                    pl_labels.append(name_pl)
                    en_labels.append(name_en)
            reg_details['hierarchy_label_pl'] = ', '.join(pl_labels)
            reg_details['hierarchy_label_en'] = ', '.join(en_labels)


class PeliasApi(BaseApi):
    def __init__(self, size=25):
        self.size = size
        super().__init__(settings.GEOCODER_URL + '/v1/')

    def autocomplete(self, text, lang='pl', layers=None):
        params = {'text': text,
                  'lang': lang,
                  'sources': 'wof',
                  'size': self.size}
        if layers:
            params['layers'] = layers
        resp = self._send_request('autocomplete', params)
        self.add_hierarchy_labels(resp)
        return resp

    def place(self, ids):
        params = {
            'ids': ','.join(ids)
        }
        return self._send_request('place', params, err_resp={})

    def add_hierarchy_labels(self, reg_data):
        for reg in reg_data['features']:
            labels = []
            for r_type in self.hierarchy_region_labels:
                type_label = r_type[:-3]
                name = reg['properties'].get(type_label)
                if name:
                    if r_type == 'localadmin_id' and not name.startswith('Gmina'):
                        name = f'Gmina {name}'
                    elif r_type == 'county_id':
                        name = f'pow. {name}'
                    elif r_type == 'region_id':
                        name = f'woj. {name}'
                    labels.append(name)
            reg['properties']['hierarchy_label'] = ', '.join(labels)

    def convert_teryt_id(self, teryt_id):
        len_mapping = {
            2: 'region',
            4: 'county',
            7: 'admin_or_locality'
        }
        try:
            region_type = len_mapping[len(teryt_id)]
        except KeyError:
            raise MalformedTerytCodeError(_(f'Malformed teryt code: {teryt_id}.'
                                            f' Provided code does not seems to refer to region, county,'
                                            f' localadmin or locality'))
        region_type = self.verify_teryt_region(teryt_id) if region_type == 'admin_or_locality' else region_type
        return f'teryt:{region_type}:{teryt_id}'

    @staticmethod
    def is_valid_simc_code(teryt_id):
        control_num = teryt_id[-1]
        base_num = teryt_id[:-1]
        id_sum = sum([(i + 2) * int(num) for i, num in enumerate(base_num)])
        check_sum = id_sum % 11
        check_sum = '0' if check_sum == 10 else str(check_sum)
        return check_sum == control_num

    def verify_teryt_region(self, teryt_id):
        return 'locality' if self.is_valid_simc_code(teryt_id) else 'localadmin'

    def convert_teryt_to_gids(self, ids):
        gids = []
        for reg_id in ids:
            gids.append(self.convert_teryt_id(reg_id))
        return gids

    def translate_teryt_to_wof_ids(self, teryt_codes):
        wof_ids = []
        if teryt_codes:
            gids = self.convert_teryt_to_gids(teryt_codes)
            places_details = self.place(gids)
            for reg in places_details['features']:
                teryt_gid = reg['properties']['gid']
                gid_elems = teryt_gid.split(':')
                wof_gid = f'{gid_elems[1]}_gid'
                region_id = reg['properties'][wof_gid].split(':')[2]
                wof_ids.append(region_id)
        return wof_ids

import string

import requests
import shapefile
from mcod import settings
from pyproj import CRS, Transformer
from requests.auth import HTTPBasicAuth


class ExtractUAddressError(Exception):
    pass


def _cut_extension(filename):
    return filename.rsplit('.', 1)


def are_shapefiles(files):
    try:
        shp_name = next(iter(_cut_extension(file)[0] for file in files if _cut_extension(file)[-1] == 'shp'))
    except StopIteration:
        return False
    shp_files, other_files, extensions = set(), set(), set()
    for file in files:
        if _cut_extension(file)[0] == shp_name:
            shp_files.add(file)
            extensions.add(_cut_extension(file)[-1])
        else:
            other_files.add(file)
    return len(extensions.intersection({'shp', 'shx', 'dbf'})) == 3 and len(shp_files) > len(other_files)


def analyze_shapefile(files):
    options = {}
    with shapefile.Reader(files[0]) as shp:
        options['charset'] = shp.encoding
        shp_type = shp.shapeTypeName

    return shp_type, options


class NoTransformationRequired(Exception):
    pass


WGS84_CRS_CODE = 4326


class ShapeTransformer:
    _transformer = None

    def __init__(self, extracted):
        try:
            prj = next(iter(f for f in extracted if f.endswith('.prj')))
            crs = CRS.from_wkt(open(prj, 'r').read())
            if crs.to_epsg() == WGS84_CRS_CODE:
                raise NoTransformationRequired
            self._transformer = Transformer.from_crs(crs, WGS84_CRS_CODE)
        except (StopIteration, NoTransformationRequired):
            pass

    def recurent_transform(self, coord_list):
        if isinstance(coord_list[0], float):
            return self._transformer.transform(*coord_list)[::-1]
        elif isinstance(coord_list[0][0], (list, tuple)):
            return tuple(self.recurent_transform(sub_list) for sub_list in coord_list)
        else:
            return tuple(self._transformer.transform(*co)[::-1] for co in coord_list)

    def transform(self, shape):
        geojson = shape.__geo_interface__
        if self._transformer is not None:
            geojson['coordinates'] = self.recurent_transform(geojson['coordinates'])
        return geojson


def _coord_list_median(coords, skip_last=False):
    if isinstance(coords[0][0], (float, int)):
        if skip_last:
            return sum(co[0] for co in coords[:-1]) / float(len(coords) - 1), \
                sum(co[1] for co in coords[:-1]) / float(len(coords) - 1)
        else:
            return sum(co[0] for co in coords) / float(len(coords)), \
                sum(co[1] for co in coords) / float(len(coords))
    else:
        sub_coords = [_coord_list_median(sub, skip_last) for sub in coords]
        return (
            sum(co[0] for co in sub_coords) / float(len(sub_coords)),
            sum(co[1] for co in sub_coords) / float(len(sub_coords))
        )


def median_point(geojson):
    if geojson['type'] == 'Point':
        return geojson['coordinates']
    elif geojson['type'] == 'GeometryCollection':
        geom_coords = [median_point(geom) for geom in geojson['geometries']]
        return (
            sum(co[0] for co in geom_coords) / float(len(geom_coords)),
            sum(co[1] for co in geom_coords) / float(len(geom_coords))
        )

    return _coord_list_median(geojson['coordinates'], skip_last=geojson['type'].endswith('Polygon'))


def _request_geocoder(text=None, **kwargs):
    try:
        params = {}
        url = f"{settings.GEOCODER_URL}/v1/search"
        if len(kwargs) == 0:
            params['text'] = text
        else:
            params = kwargs
            url += '/structured'

        response = requests.get(url, params=params,
                                auth=HTTPBasicAuth(settings.GEOCODER_USER, settings.GEOCODER_PASS))

        if response.status_code != 200:
            raise Exception()
        features = response.json().get('features')
        if features:
            return features[0].get('geometry')
    except Exception:
        pass


def first_non_digit(s):
    for c in s:
        if not c.isdigit():
            return c


def clean_house_number(number):
    if isinstance(number, str):
        number = number.lstrip(string.ascii_letters + string.whitespace + string.punctuation)\
                       .rstrip(string.whitespace + string.punctuation)
        sep = first_non_digit(number)
        if sep is None:
            return number

        left, sep, right = number.partition(sep)

        if sep not in {'\\', '/'}:
            return left

        if right.isdecimal():
            left_int, right_int = int(left), int(right)
            if 0 <= right_int - left_int <= 10:
                return number

        if right[:-1].isdecimal():
            return left

    return number


def geocode(*args, **kwargs):
    query = {}
    for kw in kwargs:
        if kw == 'address':
            query[kw] = kwargs[kw].replace('"', '')
        if kw in {'neighbourhood', 'borough', 'locality', 'county', 'region', 'postalcode', 'country'}:
            query[kw] = kwargs[kw]
    result = None
    if query:
        result = _request_geocoder(**query)
    if not result:
        result = _request_geocoder(' '.join(str(v) for v in args) + ' '.join(str(v) for v in kwargs.values()))
    return result


crs_CS92 = CRS.from_epsg(2180)
transformer_CS92 = Transformer.from_crs(crs_CS92, WGS84_CRS_CODE)


def extract_coords_from_uaddress(uaddress):
    try:
        return transformer_CS92.transform(*uaddress.split('|')[5:7])[::-1]
    except Exception:
        raise ExtractUAddressError(uaddress)

import logging
import os
import string
from io import BytesIO

import ijson
import requests
import shapefile
import xmlschema
from lxml import etree
from pyproj import CRS, Transformer
from requests.auth import HTTPBasicAuth
from tifffile import TiffFile

from mcod import settings
from mcod.lib.jsonstat import validate as jsonstat_validate

logger = logging.getLogger('mcod')


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


def is_geotiff(path):
    return path is not None and '.tif' in path and TiffFile(path).is_geotiff


def is_geojson(path):
    with open(path) as fp:
        try:
            parser = ijson.parse(fp)
            data = {}
            top_keys = ['coordinates', 'features', 'geometry', 'geometries']
            for prefix, event, value in parser:
                if (prefix, event) == ('type', 'string'):
                    data['type'] = value
                elif (prefix, event) == ('', 'map_key') and value in top_keys:
                    data[value] = True
            gtype = data.get('type')
            geo_types = ['LineString', 'MultiLineString', 'MultiPoint', 'MultiPolygon', 'Point', 'Polygon']
            return any([
                gtype in geo_types and 'coordinates' in data,
                gtype == 'Feature' and 'geometry' in data,
                gtype == 'FeatureCollection' and 'features' in data,
                gtype == 'GeometryCollection' and 'geometries' in data,
            ])
        except Exception as exc:
            logger.debug('Exception during geojson validation: {}'.format(exc))
    return False


def is_gpx(path, content_type):
    return path is not None and content_type == 'xml' and is_valid_gpx(path)


def is_kml(path, content_type, is_extracted=False):
    if content_type == 'xml' and path.lower().endswith('.kml'):
        if is_extracted:
            return True
        try:
            xsd_path = 'http://schemas.opengis.net/kml/2.2.0/ogckml22.xsd'
            schema = xmlschema.XMLSchema(xsd_path)
            schema.validate(path)
            return True
        except Exception as exc:
            logger.debug('Exception during KML file validation: {}'.format(exc))
            raise exc
    return False


def is_valid_gpx(file_path):
    try:
        parsed_xml = etree.parse(file_path)
        root = parsed_xml.getroot()
        version = root.get('version')
        if version == '1.1':
            schema_path = settings.GPX_11_SCHEMA_PATH
        elif version == '1.0':
            schema_path = settings.GPX_10_SCHEMA_PATH
        else:
            schema_path = None
        if not schema_path or not root.tag.endswith('gpx'):
            return False
        gpx_schema_doc = etree.parse(schema_path)
        gpx_schema = etree.XMLSchema(gpx_schema_doc)
        gpx_schema.assertValid(parsed_xml)
        return True
    except Exception as exc:
        logger.debug('Exception during gpx validation: {}'.format(exc))
        return False


def has_geotiff_files(files):
    base_tiff_files = {_cut_extension(f)[-1]: f for f in files if _cut_extension(f)[-1] in ['tiff', 'tif', 'tfw']}
    try:
        tif_file = base_tiff_files['tif']
    except KeyError:
        tif_file = base_tiff_files.get('tiff')
    return ('tfw' in base_tiff_files and tif_file is not None) or is_geotiff(tif_file)


def is_json_stat(source):
    if isinstance(source, str):
        source = open(os.path.realpath(source))
    elif isinstance(source, bytes):
        source = BytesIO(source)
    source.seek(0)
    try:
        return jsonstat_validate(source.read())
    except Exception as exc:
        logger.debug('Exception during JSON-stat validation: {}'.format(exc))
        return False


def analyze_shapefile(files):
    options = {}
    with shapefile.Reader(files[0]) as shp:
        options['charset'] = shp.encoding
        shp_type = shp.shapeTypeName
        logger.debug(f'  recognized shapefile {shp_type}, {options}')
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


def check_geodata(path, content_type, family, is_extracted=False):
    if is_geotiff(path):
        content_type += ';application=geotiff'
    if content_type in ('json', 'plain') and is_geojson(path):
        family = 'application'
        content_type = 'geo+json'
    if is_gpx(path, content_type):
        family = 'application'
        content_type = 'gpx+xml'
    if is_kml(path, content_type, is_extracted):
        family = 'application'
        content_type = 'vnd.google-earth.kmz' if is_extracted else 'vnd.google-earth.kml+xml'
    return content_type, family

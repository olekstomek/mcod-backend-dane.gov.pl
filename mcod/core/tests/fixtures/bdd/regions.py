import pytest
from django.apps import apps
from pytest_bdd import then


@pytest.fixture
def main_regions_response():
    return {"101752777": {"id": 101752777, "name": "Warszawa", "placetype": "locality", "rank": {"min": 9, "max": 10},
                          "population": 1702139, "lineage":
                              [{"continent_id": 102191581, "country_id": 85633723, "county_id": 1477743805,
                                "localadmin_id": 1125365875, "locality_id": 101752777, "region_id": 85687257}],
                          "geom": {"area": 0.068027, "bbox": "20.851688,52.09785,21.271151,52.368154", "lat": 52.237695,
                                   "lon": 21.005427},
                          "names": {"eng": ["Warsaw"], "pol": ["Warszawa"]}},
            "1309742673": {"id": 1309742673, "name": "Wola Kosowska", "placetype": "locality",
                           "rank": {"min": 9, "max": 10}, "lineage":
                               [{"continent_id": 102191581, "country_id": 85633723, "county_id": 102079911,
                                 "localadmin_id": 1125356333, "locality_id": 1309742673, "region_id": 85687257}],
                           "geom": {"bbox": "20.82012,52.03683,20.86012,52.07683", "lat": 52.05683, "lon": 20.84012},
                           "names": {"pol": ["Wólka Kosowska"]}}}


@pytest.fixture
def additional_regions_response():
    return {"85687257": {"id": 85687257, "name": "Mazowieckie", "abbr": "MZ", "placetype": "region",
                         "rank": {"min": 14, "max": 15}, "population": 5268660,
                         "lineage": [{"continent_id": 102191581, "country_id": 85633723, "region_id": 85687257}],
                         "geom": {"area": 4.689476, "bbox": "19.259214,51.013112,23.128409,53.481806", "lat": 52.512784,
                                  "lon": 21.125296}, "names": {"eng": ["Mazowieckie"], "pol": ["mazowieckie"]}},
            "102079911": {"id": 102079911, "name": "Piaseczyński", "placetype": "county",
                          "rank": {"min": 12, "max": 13}, "lineage":
                              [{"continent_id": 102191581, "country_id": 85633723,
                                "county_id": 102079911, "region_id": 85687257}],
                          "geom": {"area": 0.081285, "bbox": "20.685116,51.887954,21.281262,52.144728",
                                   "lat": 52.020263, "lon": 21.044128},
                          "names": {"fra": ["Piaseczno"], "pol": ["Piaseczyński"]}},
            "1125356333": {"id": 1125356333, "name": "Lesznowola", "placetype": "localadmin",
                           "rank": {"min": 11, "max": 12}, "lineage":
                               [{"continent_id": 102191581, "country_id": 85633723, "county_id": 102079911,
                                 "localadmin_id": 1125356333, "region_id": 85687257}],
                           "geom": {"area": 0.009084, "bbox": "20.809666165,52.021535516,21.035504392,52.120636077",
                                    "lat": 52.090032, "lon": 20.941123}, "names": {"pol": ["Lesznowola"]}},
            "1125365875": {"id": 1125365875, "name": "Gmina Warszawa", "placetype": "localadmin",
                           "rank": {"min": 11, "max": 12}, "lineage":
                               [{"continent_id": 102191581, "country_id": 85633723, "county_id": 1477743805,
                                 "localadmin_id": 1125365875, "region_id": 85687257}],
                           "geom": {"area": 0.068027, "bbox": "20.851688337,52.097849611,21.271151295,52.368153943",
                                    "lat": 52.2331, "lon": 21.0614},
                           "names": {"deu": ["Warschau"], "eng": ["Warsaw"], "fra": ["Varsovie"],
                                     "pol": ["Gmina Warszawa"]}},
            "1477743805": {"id": 1477743805, "name": "Warszawa", "placetype": "county", "rank": {"min": 12, "max": 13},
                           "lineage": [{"continent_id": 102191581, "country_id": 85633723, "county_id": 1477743805,
                                        "region_id": 85687257}],
                           "geom": {"area": 0.068027, "bbox": "20.851688,52.09785,21.271151,52.368154",
                                    "lat": 52.245513, "lon": 21.001878},
                           "names": {"fra": ["Varsovie"], "pol": ["Warszawa"]}}}


@pytest.fixture
def main_region():
    region = apps.get_model('regions', 'Region')
    return region.objects.create(
        name='Warszawa',
        region_id=101752777,
        region_type='locality',
        lat=52.237695,
        lng=21.005427,
        bbox=[20.851688, 52.09785, 21.271151, 52.368154],
        geonames_id=756135
    )


@pytest.fixture
def additional_regions(additional_regions_response):
    to_create_regions = ["1477743805", "1125365875", "85687257"]
    region = apps.get_model('regions', 'Region')
    created_regions = region.objects.bulk_create([region(
        region_id=reg_id,
        region_type=additional_regions_response[reg_id]['placetype'],
        name_pl=additional_regions_response[reg_id]['names']['pol'][0] if
        additional_regions_response[reg_id]['names'].get('pol') else additional_regions_response[reg_id]['name'],
        name_en=additional_regions_response[reg_id]['names']['eng'][0] if
        additional_regions_response[reg_id]['names'].get('eng') else additional_regions_response[reg_id]['name'],
        bbox=additional_regions_response[reg_id]['geom']['bbox'].split(','),
        lat=additional_regions_response[reg_id]['geom']['lat'],
        lng=additional_regions_response[reg_id]['geom']['lon']
    ) for reg_id in to_create_regions])
    return created_regions


@then('resource has assigned main and additional regions')
def resource_has_assigned_regions():
    model = apps.get_model('resources', 'resource')
    res = model.objects.all().last()
    expected_main = [101752777, 1309742673]
    expected_additional = [85687257, 102079911, 1125356333, 1125365875, 1477743805]
    main_regions = list(res.regions.filter(
        resourceregion__is_additional=False
    ).values_list('region_id', flat=True).order_by('region_id'))
    additional_regions = list(res.regions.filter(
        resourceregion__is_additional=True
    ).values_list('region_id', flat=True).order_by('region_id'))
    assert main_regions == expected_main
    assert additional_regions == expected_additional

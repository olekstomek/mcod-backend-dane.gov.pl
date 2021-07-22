# import shapefile
# from mcod.resources.geo import shp2geojson, shapefile2geojson
#

# class TestGeo:
#     def test_shparch2geojson(self, shapefile_arch):
#         gj = shapefile2geojson(shapefile_arch)
#
#         assert len(gj.features) == 1
#         assert len(gj.features[0]['properties']) == 18
#
#     def test_shapefile2geojson(self, shapefile_world):
#         gj = shapefile2geojson(shapefile_world[0])
#
#         assert len(gj.features) == 246
#         assert len(gj.features[0]['properties']) == 11
#
#     def test_shp2geojson(self, shapefile_world):
#         with shapefile.Reader(shapefile_world[0]) as shp:
#             gj = shp2geojson(shp)
#
#             assert len(gj.features) == len(shp.shapes())
#             assert len(gj.features[0]['properties']) == len(shp.record(0))

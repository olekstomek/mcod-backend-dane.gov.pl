import factory

from mcod.regions import models

POLISH_CENTER_COORDINATES = [52.04, 19.29]
POLISH_CENTER_GEONAME_ID = 3_089_173


class RegionFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("city", locale="pl_PL")
    hierarchy_label = factory.LazyAttribute(lambda obj: f"Polska | {obj.name}")
    region_id = factory.Sequence(lambda n: str(n).zfill(7))

    region_type = factory.Faker("random_element", elements=[t[0] for t in models.Region.REGION_TYPES])

    lat = factory.Faker("coordinate", center=POLISH_CENTER_COORDINATES[0], radius=2.0)
    lng = factory.Faker("coordinate", center=POLISH_CENTER_COORDINATES[1], radius=4.0)

    @factory.lazy_attribute
    def bbox(self):
        # Create a small square (e.g., +/- 0.1 degree) around the center
        buffer = 0.1
        return [
            float(self.lng) - buffer,  # min_lng
            float(self.lat) - buffer,  # min_lat
            float(self.lng) + buffer,  # max_lng
            float(self.lat) + buffer,  # max_lat
        ]

    geonames_id = factory.Sequence(lambda n: POLISH_CENTER_GEONAME_ID + n)  # e.g. https://www.geonames.org/3089173

    class Meta:
        model = models.Region
        django_get_or_create = ("region_id",)

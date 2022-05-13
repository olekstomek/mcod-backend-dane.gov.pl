import json
import os
import tempfile
import uuid
from io import BytesIO

import factory

from mcod.core.registries import factories_registry
from mcod.datasets.factories import DatasetFactory
from mcod.resources import models

_RESOURCE_TYPES = [i[0] for i in models.RESOURCE_TYPE]
_TASK_STATUSES = ['SUCCESS', 'NOT AVAILABLE', 'ERROR']

data = b"""\
col1,col2,col3
1,3,foo
2,5,bar
-1,7,baz"""


def get_csv_file():
    return BytesIO(
        b"\n".join(
            [b"col1,col2,col3",
             b"1,3,foo",
             b"2,5,bar",
             b"-1,7,baz"
             ]
        )
    )


def get_csv_file2():
    fp = tempfile.TemporaryFile()
    fp.write(b'Hello world!')
    fp.close()
    return fp


class ResourceFileFactory(factory.django.DjangoModelFactory):
    file = factory.django.FileField(from_func=get_csv_file, filename='{}.csv'.format(str(uuid.uuid4())))
    format = 'csv'
    openness_score = factory.Faker('random_int', min=1, max=5)
    resource = factory.SubFactory('mcod.resources.factories.ResourceFactory')
    is_main = True
    mimetype = 'application/csv'

    @classmethod
    def _create(cls, model, *args, **kwargs):
        from mcod.core.tests.fixtures import adapter
        from mcod.resources.link_validation import session
        file = kwargs.get('file')
        format = kwargs.get('format')
        content_type = kwargs.pop('content_type', None)
        if content_type or kwargs['resource'].link:
            if content_type is None:
                content_type = 'application/csv'
            adapter.register_uri('GET', kwargs['resource'].link,
                                 content=file.read(),
                                 headers={'Content-Type': content_type})
            session.mount(kwargs['resource'].link, adapter)
        if hasattr(file, 'name'):
            filename = file.name
        else:
            filename = file
        ext = os.path.splitext(filename)[1][1:]
        if ext != format:
            kwargs['format'] = ext
        return super()._create(model, *args, **kwargs)

    class Meta:
        model = models.ResourceFile


class ResourceFactory(factory.django.DjangoModelFactory):
    title = factory.Faker('text', max_nb_chars=100, locale='pl_PL')
    description = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')
    views_count = factory.Faker('random_int', min=0, max=500)
    downloads_count = factory.Faker('random_int', min=0, max=500)
    main_file = factory.RelatedFactory(ResourceFileFactory, factory_related_name='resource')
    link = factory.LazyAttribute(lambda obj: 'https://test.mcod/media/resources/{}'.format(str(uuid.uuid4())))
    format = 'CSV'
    type = factory.Faker('random_element', elements=_RESOURCE_TYPES)
    openness_score = factory.Faker('random_int', min=1, max=5)
    dataset = factory.SubFactory(DatasetFactory)
    forced_api_type = False
    forced_file_type = False
    data_date = factory.Faker('past_date', start_date="-7d")

    @factory.post_generation
    def link_tasks(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.link_tasks.add(task)

    @factory.post_generation
    def file_tasks(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.file_tasks.add(task)

    @factory.post_generation
    def data_tasks(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.data_tasks.add(task)

    @factory.post_generation
    def dataset_set(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for dataset in extracted:
                self.dataset_set.add(dataset)

    @classmethod
    def _create(cls, model, *args, file=None, link=None, **kwargs):
        return super()._create(model, *args, link=link, **kwargs)

    class Meta:
        model = models.Resource
        django_get_or_create = ('title',)


def json_sequence(number):
    return {
        'x': f'col{number}',
        'y': f'col{number + 1}',
    }


class ChartFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('text', max_nb_chars=200, locale='pl_PL')
    chart = factory.Sequence(json_sequence)
    resource = factory.SubFactory(ResourceFactory)
    is_default = True

    class Meta:
        model = models.Chart


class SupplementFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('text', max_nb_chars=200, locale='pl_PL')
    file = factory.django.FileField(from_func=get_csv_file, filename='{}.txt'.format(str(uuid.uuid4())))
    resource = factory.SubFactory(ResourceFactory)
    order = 0
    language = 'pl'

    class Meta:
        model = models.Supplement


class TaskResultFactory(factory.django.DjangoModelFactory):
    task_id = factory.Faker('uuid4')
    status = factory.Faker('random_element', elements=_TASK_STATUSES)
    result = factory.Faker('paragraph', nb_sentences=3, variable_nb_sentences=True, locale='pl_PL')

    class Meta:
        model = models.TaskResult

    @factory.post_generation
    def data_task_resources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.data_task_resources.add(task)

    @factory.post_generation
    def file_task_resources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.file_task_resources.add(task)

    @factory.post_generation
    def link_task_resources(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for task in extracted:
                self.link_task_resources.add(task)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if isinstance(kwargs.get('result'), dict):
            kwargs['result'] = json.dumps(kwargs['result'])
        return kwargs


factories_registry.register('resource', ResourceFactory)
factories_registry.register('resourcefile', ResourceFileFactory)
factories_registry.register('chart', ChartFactory)
factories_registry.register('task result', TaskResultFactory)
factories_registry.register('supplement', SupplementFactory)

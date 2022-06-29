from django.apps import apps
from pytest_bdd import given, parsers, then, when

from mcod.applications.factories import ApplicationFactory
from mcod.datasets.factories import DatasetFactory
from mcod.resources.factories import ResourceFactory


@given('application')
def application():
    org = ApplicationFactory.create()
    return org


@given('removed application')
def removed_application():
    org = ApplicationFactory.create(is_removed=True, title='Removed application')
    return org


@given(parsers.parse('draft application with id {application_id:d}'))
def draft_application_with_id(application_id):
    org = ApplicationFactory.create(id=application_id, title='Draft application {}'.format(application_id),
                                    status='draft')
    return org


@given(parsers.parse('removed application with id {application_id:d}'))
def removed_application_with_id(application_id):
    org = ApplicationFactory.create(id=application_id, title='Removed application {}'.format(application_id),
                                    is_removed=True)
    return org


@given('application with datasets')
def application_with_datasets():
    org = ApplicationFactory.create()
    DatasetFactory.create_batch(2, application=org)
    return org


@given(parsers.parse('application with id {application_id:d} and {num:d} datasets'))
def application_with_id_and_datasets(application_id, num):
    application = ApplicationFactory.create(
        id=application_id, title='application {} with datasets'.format(application_id))
    datasets = DatasetFactory.create_batch(num, applications=(application,))
    for dataset in datasets:
        ResourceFactory.create_batch(3, dataset=dataset)
    return application


@given(parsers.parse('{num:d} applications'))
def applications(num):
    return ApplicationFactory.create_batch(num)


@given('4 applications set to be displayed on main page')
@given('featured applications')
def featured_applications():
    return [
        ApplicationFactory.create(main_page_position=pos)
        for pos in range(1, 5)
    ]


@then(parsers.parse("{num:d} featured applications are returned"))
def x_featured_applications_are_returned(num, context):
    applications = context.response.json['data']
    possible_values = {1, 2, 3, 4}
    app_positions = {app['attributes']['main_page_position'] for app in applications}
    assert app_positions.issubset(possible_values) and len(app_positions) == num


@when(parsers.parse('remove application with id {application_id}'))
@then(parsers.parse('remove application with id {application_id}'))
def remove_application(application_id):
    model = apps.get_model('applications', 'application')
    inst = model.objects.get(pk=application_id)
    inst.is_removed = True
    inst.save()


@when(parsers.parse('restore application with id {application_id}'))
@then(parsers.parse('restore application with id {application_id}'))
def restore_application(application_id):
    model = apps.get_model('applications', 'application')
    inst = model.raw.get(pk=application_id)
    inst.is_removed = False
    inst.save()


@when(parsers.parse('change status to {status} for application with id {application_id}'))
@then(parsers.parse('change status to {status} for application with id {application_id}'))
def change_application_status(status, application_id):
    model = apps.get_model('applications', 'application')
    inst = model.objects.get(pk=application_id)
    inst.status = status
    inst.save()

from django.apps import apps
from pytest_bdd import given, when, then
from pytest_bdd import parsers

from mcod.showcases.factories import ShowcaseFactory
from mcod.datasets.factories import DatasetFactory
from mcod.resources.factories import ResourceFactory


@given(parsers.parse('showcase'))
def showcase():
    return ShowcaseFactory.create()


# @given(parsers.parse('draft showcase'))
# def draft_showcase():
#     return ShowcaseFactory.create(status='draft', title='Draft showcase')


@given(parsers.parse('removed showcase'))
def removed_showcase():
    return ShowcaseFactory.create(is_removed=True, title='Removed showcase')


# @given(parsers.parse('showcase with id {showcase_id:d}'))
# def showcase_with_id(application_id):
#     return ShowcaseFactory.create(id=showcase_id, title='showcase %s' % showcase_id)


@given(parsers.parse('second showcase with id {showcase_id:d}'))
def second_showcase_with_id(showcase_id):
    return ShowcaseFactory.create(id=showcase_id, title='Second showcase %s' % showcase_id)


@given(parsers.parse('another showcase with id {showcase_id:d}'))
def another_showcase_with_id(showcase_id):
    return ShowcaseFactory.create(id=showcase_id, title='Another showcase %s' % showcase_id)


@given(parsers.parse('draft showcase with id {showcase_id:d}'))
def draft_showcase_with_id(showcase_id):
    return ShowcaseFactory.create(
        id=showcase_id, title='Draft showcase {}'.format(showcase_id), status='draft')


@given(parsers.parse('removed showcase with id {showcase_id:d}'))
def removed_showcase_with_id(showcase_id):
    return ShowcaseFactory.create(
        id=showcase_id, title='Removed showcase {}'.format(showcase_id), is_removed=True)


@given(parsers.parse('showcase with datasets'))
def showcase_with_datasets():
    showcase = ShowcaseFactory.create()
    DatasetFactory.create_batch(2, showcase=showcase)
    return showcase


@given(parsers.parse('showcase with id {showcase_id:d} and {num:d} datasets'))
def showcase_with_id_and_datasets(showcase_id, num):
    showcase = ShowcaseFactory.create(
        id=showcase_id, title='showcase {} with datasets'.format(showcase_id))
    datasets = DatasetFactory.create_batch(num, showcases=(showcase,))
    for dataset in datasets:
        ResourceFactory.create_batch(3, dataset=dataset)
    return showcase


@given(parsers.parse('3 showcases'))
def showcases():
    return ShowcaseFactory.create_batch(3)


@given(parsers.parse('{num:d} showcases'))
def x_showcases(num):
    return ShowcaseFactory.create_batch(num)


@given('4 showcases set to be displayed on main page')
@given('featured showcases')
def featured_showcases():
    return [
        ShowcaseFactory.create(main_page_position=pos)
        for pos in range(1, 5)
    ]


@then(parsers.parse("{num:d} featured showcases are returned"))
def x_featured_showcases_are_returned(num, context):
    showcases = context.response.json['data']
    possible_values = {1, 2, 3, 4}
    positions = {x['attributes']['main_page_position'] for x in showcases}
    assert positions.issubset(possible_values) and len(positions) == num


@when(parsers.parse('remove showcase with id {showcase_id}'))
@then(parsers.parse('remove showcase with id {showcase_id}'))
def remove_showcase(showcase_id):
    model = apps.get_model('showcases.Showcase')
    obj = model.objects.get(pk=showcase_id)
    obj.is_removed = True
    obj.save()


@when(parsers.parse('restore showcase with id {showcase_id}'))
@then(parsers.parse('restore showcase with id {showcase_id}'))
def restore_showcase(showcase_id):
    model = apps.get_model('showcases.Showcase')
    obj = model.raw.get(pk=showcase_id)
    obj.is_removed = False
    obj.save()


@when(parsers.parse('change status to {status} for showcase with id {showcase_id}'))
@then(parsers.parse('change status to {status} for showcase with id {showcase_id}'))
def change_showcase_status(status, showcase_id):
    model = apps.get_model('showcases.Showcase')
    obj = model.objects.get(pk=showcase_id)
    obj.status = status
    obj.save()

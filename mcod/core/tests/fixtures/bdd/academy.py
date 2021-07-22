import datetime
import json

from dateutil.relativedelta import relativedelta
from django.utils import timezone
from pytest_bdd import given, parsers, then

from mcod.academy.factories import CourseFactory, CourseModuleFactory
from mcod.academy.models import Course


@given(parsers.parse('course with id {course_id:d}'))
def course_with_id(course_id):
    return CourseFactory.create(id=course_id, title='Course with id: %s' % course_id)


@given(parsers.parse('finished course with id {course_id:d}'))
def finished_course_with_id(course_id):
    _course = CourseFactory.create(id=course_id, title='Finished course with id {}'.format(course_id))
    data = {
        'course': _course,
        'start': timezone.now().date() - relativedelta(days=3),
    }
    CourseModuleFactory.create(**data)
    _course.save()
    return _course


@given(parsers.parse('planned course with id {course_id:d}'))
def planned_course_with_id(course_id):
    _course = CourseFactory.create(id=course_id, title='Planned course with id {}'.format(course_id))
    data = {
        'course': _course,
        'start': timezone.now().date() + relativedelta(days=3),
    }
    CourseModuleFactory.create(**data)
    _course.save()
    return _course


@given(parsers.parse('current course with id {course_id:d}'))
def current_course_with_id(course_id):
    _course = CourseFactory.create(id=course_id, title='Current course with id {}'.format(course_id))
    data = {
        'course': _course,
        'start': timezone.now().date(),
    }
    CourseModuleFactory.create(**data)
    _course.save()
    return _course


@then(parsers.parse('course with title {course_title} contains data {data_str}'))
def course_with_title_attribute_is(course_title, data_str):
    course = Course.objects.get(title=course_title)
    data = json.loads(data_str)
    for attr_name, attr_value in data.items():
        course_attr = getattr(course, attr_name)
        if isinstance(course_attr, datetime.date):
            course_attr = str(course_attr)
        assert course_attr == attr_value, f'Course attribute {course_attr} should be {attr_value}'


@given('<planned> planned academy courses')
def planned_courses(planned: int):
    return CourseModuleFactory.create_batch(
        size=int(planned),
        start=timezone.now().date() + relativedelta(days=3)
    )


@given('<current> current academy courses')
def current_courses(current: int):
    return CourseModuleFactory.create_batch(
        size=int(current),
        start=timezone.now().date()
    )


@given('<finished> finished academy courses')
def finished_courses(finished: int):
    return CourseModuleFactory.create_batch(
        size=int(finished),
        start=timezone.now().date() - relativedelta(days=3)
    )

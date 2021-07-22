import json
from pytest_bdd import given, parsers

from mcod.schedules.factories import (  # noqa
    ScheduleFactory,
    UserScheduleFactory,
    UserScheduleItemFactory,
    UserScheduleItemCommentFactory,
)

from mcod.core.tests.fixtures.bdd.common import create_object


@given(parsers.parse('{num:d} user schedule items with state {state}'))
def x_user_schedule_items(num, state):
    schedule = ScheduleFactory(state=state)
    user_schedule = UserScheduleFactory(schedule=schedule)
    return UserScheduleItemFactory.create_batch(num, user_schedule=user_schedule)


@given(parsers.parse('schedule data created with {params}'))
def schedule_data(params):
    kwargs = json.loads(params)

    schedule_id = kwargs.pop('schedule_id')
    schedule_state = kwargs.pop('schedule_state', None)
    schedule_is_blocked = kwargs.pop('schedule_is_blocked', None)
    user_id = kwargs.pop('user_id', None)
    user_schedule_id = kwargs.pop('user_schedule_id', None)
    user_schedule_item_id = kwargs.pop('user_schedule_item_id', None)
    recommendation_state = kwargs.pop('recommendation_state', None)
    comment_id = kwargs.pop('comment_id', None)

    schedule_kwargs = {}
    if schedule_state:
        schedule_kwargs['state'] = schedule_state
    if schedule_is_blocked:
        schedule_kwargs['is_blocked'] = schedule_is_blocked
    schedule = create_object('schedule', schedule_id, **schedule_kwargs, **kwargs)

    if user_schedule_id:
        user_schedule_kwargs = {'schedule': schedule}
        if user_id:
            user_schedule_kwargs['user_id'] = user_id
        user_schedule = create_object('user_schedule', user_schedule_id, **user_schedule_kwargs, **kwargs)

        if user_schedule_item_id:
            user_schedule_item_kwargs = {'user_schedule': user_schedule}
            if recommendation_state:
                user_schedule_item_kwargs['recommendation_state'] = recommendation_state
            user_schedule_item = create_object(
                'user_schedule_item', user_schedule_item_id, **user_schedule_item_kwargs, **kwargs)
            if comment_id:
                comment_kwargs = {'user_schedule_item': user_schedule_item}
                if user_id:
                    comment_kwargs['created_by_id'] = user_id
                create_object('user_schedule_item_comment', comment_id, **comment_kwargs, **kwargs)

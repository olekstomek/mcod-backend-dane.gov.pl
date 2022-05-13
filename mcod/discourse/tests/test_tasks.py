from mcod.discourse.tasks import user_logout_task, user_sync_task
from mcod.discourse.tests.utils import discourse_response_mocker


def test_user_sync_task_deactivate_user(inactive_admin):
    with discourse_response_mocker(inactive_admin):
        result = user_sync_task(inactive_admin.pk)
    assert result == {'result': 'ok'}


def test_user_sync_task_activate_user(admin):
    with discourse_response_mocker(admin):
        result = user_sync_task(admin.pk)
    admin.refresh_from_db()
    assert admin.discourse_user_name == 'admin'
    assert admin.discourse_api_key == '1234567'
    assert result == {'result': 'ok'}


def test_user_logout_task(admin):
    with discourse_response_mocker(admin):
        result = user_logout_task(admin.pk)
    assert result == {'result': 'ok'}

from django.test import override_settings

from mcod.celeryapp import app as celery_app, get_beat_schedule
from mcod.settings.base import CELERY_TASK_DEFAULT_QUEUE, CELERY_TASK_ROUTES


def test_all_beat_tasks_have_queue_defined():
    """Check if all tasks running by Celery Beat (also monthly tasks)
    have defined queue other than the `default`.
    """
    celery_app.conf.beat_schedule = get_beat_schedule(enable_monthly_reports=True)
    missing_or_default_tasks = []

    for name, task in celery_app.conf.beat_schedule.items():
        queue = task.get("options", {}).get("queue")
        if not queue or queue == "default":
            missing_or_default_tasks.append(name)

    assert not missing_or_default_tasks


@override_settings(
    CELERY_TASK_DEFAULT_QUEUE=CELERY_TASK_DEFAULT_QUEUE,
    CELERY_TASK_ROUTES=CELERY_TASK_ROUTES,
)
def test_all_nonbeat_tasks_have_queue_defined():
    """Check if all tasks not runnning by Celery Beat,
    have defined queue other than the `default`.
    """
    router = celery_app.amqp.router
    missing_or_default_tasks = []

    beat_task_names = {val["task"] for val in get_beat_schedule(enable_monthly_reports=True).values()}

    for name in celery_app.tasks:
        if name.startswith("celery."):
            continue  # internal celery tasks
        if name.startswith("test_") or ".tests." in name:
            continue  # celery test tasks
        if name in beat_task_names:
            continue  # celery beat tasks

        route = router.route({}, name)
        queue = route.get("queue", "default")
        queue_name = queue.name if hasattr(queue, "name") else queue
        if queue_name == "default":
            missing_or_default_tasks.append(name)

    assert not missing_or_default_tasks

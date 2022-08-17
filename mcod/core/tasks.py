import functools
import logging

from celery import shared_task
from django.db import transaction
from kombu.utils import uuid

from mcod.unleash import is_enabled

logger = logging.getLogger('mcod')


def atomic_shared_task(*task_args, commit_on_errors=None, **task_kwargs):
    def outer(func):
        @functools.wraps(func)
        def atomic_func(*args, **kwargs):
            exception = None
            with transaction.atomic():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if commit_on_errors is None or e.__class__ not in commit_on_errors:
                        raise
                    exception = e
            if exception is not None:
                raise exception

        return shared_task(atomic_func, **task_kwargs)
    if len(task_args) == 1 and callable(task_args[0]):
        return outer(func=task_args[0])  # ex. @atomic_shared_task
    return outer  # ex. @atomic_shared_task(base=Singleton)


def extended_shared_task(*task_args, atomic=False, commit_on_errors=None, **task_kwargs):
    extended_shared_task_enabled = is_enabled('S55_extended_shared_task.be')

    def outer(func):
        if atomic and extended_shared_task_enabled:
            task = atomic_shared_task(func, commit_on_errors=commit_on_errors, **task_kwargs)
        else:
            task = shared_task(func, **task_kwargs)
        if not hasattr(task, 'apply_async_on_commit'):
            def apply_async_on_commit(self, *proxy_args, countdown=None, force_enabled=False, **proxy_kwargs):
                if extended_shared_task_enabled or force_enabled:
                    task_id = uuid()
                    transaction.on_commit(lambda: self.apply_async(*proxy_args, task_id=task_id, **proxy_kwargs))
                    return task_id
                return self.apply_async(*proxy_args, countdown=countdown, **proxy_kwargs)

            def s(self, *proxy_args, **proxy_kwargs):
                signature = self.signature(proxy_args, proxy_kwargs)
                if not hasattr(signature, 'apply_async_on_commit'):
                    signature.__class__.apply_async_on_commit = apply_async_on_commit
                return signature

            task.__class__.s = s
            task.__class__.apply_async_on_commit = apply_async_on_commit

        return task
    if len(task_args) == 1 and callable(task_args[0]):
        return outer(func=task_args[0])  # ex. @extended_shared_task
    return outer  # ex. @extended_shared_task(base=Singleton)

import functools
import logging
import warnings
from typing import Callable, Tuple, Type, Union

from celery import Task, shared_task
from celery.local import Proxy
from django.db import transaction

base_logger = logging.getLogger("mcod.tasks")

Exceptions = Tuple[Type[Exception], ...]
CeleryTask = Callable  # type alias for functions decorated as celery task


class NotSet:
    def __bool__(self):
        return False

    def __str__(self):
        return "NotSet"


not_set = NotSet()

FIVE_MINUTES = 5 * 60


def _never_retry(e: Exception) -> bool:
    return False


class SharedTask:
    """
    Decorator over Celery tasks
    Usage:
        @SharedTask()
        def update_graph_task(task: Task, app_label, object_name, instance_id):
            ...
    Functionalities:
    - retry for error handlers

    Dependencies:
    1. atomic should be innermost (modifies the execution of the func, not of Celery)
    2. retry_on_lambda should be idempotent and can't raise

    Args:
        atomic: Wraps your function in Django's `transaction.atomic` block.
        commit_on_errors: Allows to commit transaction even if some Python exception occurs.
            Warning: This won't commit transactions aborted by the database.
            If set - implies `atomic`.
        max_retries: See Celery docs - number of times to retry the task. Your function will run at most `1+max_retries` times
        retry_on_errors: Primary mechanism for retries - if an exception from this tuple is raised - we'll retry the task
        retry_on_lambda: A callable to decide if retry is possible.
            This lambda needs to accept an Exception as the first and only arg, but you're free to check unrelated conditions too.
            Complimentary to `retry_on_errors`
        retry_countdown: For how many seconds celery will delay the task's retry
        bind: See Celery docs - will inject task as a first argument.
            The decorator will set it to True either way if you need retries.
        **celery_kwargs: The rest of arguments are passed verbatim to celery.shared_task
    """

    def __init__(
        self,
        *,
        atomic=False,
        commit_on_errors: Exceptions = tuple(),
        max_retries: Union[NotSet, int] = not_set,
        retry_on_errors: Exceptions = tuple(),
        retry_on_lambda: Callable[[Exception], bool] = _never_retry,
        retry_countdown: int = FIVE_MINUTES,
        bind: bool = False,
        **celery_kwargs,
    ):
        self.commit_on_errors = commit_on_errors
        self.atomic = atomic

        self.max_retries = max_retries
        self.retry_on_errors = retry_on_errors
        self.retry_on_lambda = retry_on_lambda
        self.retry_countdown = retry_countdown

        self.bind = bind
        self.celery_kwargs = celery_kwargs

    def _validate_args(self, func: Callable):
        prefix = f"{func.__name__}: "
        if self.commit_on_errors and not self.atomic:
            warnings.warn(f"{prefix} commit_on_errors implies atomic. Consider adding atomic=True for clarity")
        if self.max_retries:
            _has_roe = bool(self.retry_on_errors)
            _has_rol = self.retry_on_lambda is not _never_retry
            if not (_has_roe or _has_rol):
                raise ValueError(f"{prefix} Either retry_on_errors or retry_on_lambda has to be set")
            if _has_roe and _has_rol:
                warnings.warn(f"{prefix} retry_on_errors has precedence over retry_on_lambda")
        if self.retry_on_lambda(Exception()) not in (True, False):
            raise ValueError(f"{prefix} retry_on_lambda didn't return boolean when checked")

    def __call__(self, func: Callable) -> CeleryTask:
        return self.decorate(func)

    def decorate(self, func: Callable) -> CeleryTask:
        self._validate_args(func)
        self._check_is_not_shared_task(func)

        _needs_atomic = bool(self.atomic or self.commit_on_errors)
        if _needs_atomic is True:
            func = self._add_atomic(func)

        _kwargs_for_shared_task = {
            **self.celery_kwargs,
        }  # these are passed to the celery.shared_task
        _needs_retry = bool(self.max_retries)
        _needs_bind = self.bind is True or _needs_retry
        if _needs_bind:
            _kwargs_for_shared_task["bind"] = True
        if _needs_retry:
            _kwargs_for_shared_task["max_retries"] = self.max_retries
            func = self._add_retries(func)
        task: CeleryTask = shared_task(**_kwargs_for_shared_task)(func)
        del func
        return task

    def _add_atomic(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def atomic_func(*args, **kwargs):
            _logger = base_logger.getChild(func.__name__)
            with transaction.atomic():
                try:
                    return func(*args, **kwargs)
                except self.commit_on_errors as e:
                    _logger.warning(f"{func.__name__} raised {e} - transaction commits")
                    exception = e
                except Exception as e:
                    _logger.warning(f"{func.__name__} raised {e} - transaction rollbacks")
                    raise
            # reraise outside of transaction
            raise exception

        return atomic_func

    def _add_retries(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def inner(task: Task, *args, **kwargs):
            _logger = base_logger.getChild(func.__name__)
            try:
                if self.bind:
                    result = func(task, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                if task.request.retries:
                    _logger.warning("No more retries - success")
                return result
            except self.retry_on_errors as retryable_exc:
                _logger.warning(f"Retry {task.request.retries}/{task.max_retries} due to {repr(retryable_exc)}")
                raise task.retry(countdown=self.retry_countdown, exc=retryable_exc)
            except Exception as exc:
                if self.retry_on_lambda(exc):
                    _logger.warning(f"Retry {task.request.retries}/{task.max_retries} due to {repr(exc)}")
                    raise task.retry(countdown=self.retry_countdown, exc=exc)
                else:
                    _logger.error(f"{task.name}: Won't retry ({task.request.retries}/{task.max_retries}) due to {repr(exc)}")
                    raise exc

        return inner

    def _check_is_not_shared_task(self, func: Union[Callable, CeleryTask]) -> None:
        _is_shared_task = isinstance(func, Proxy)
        if _is_shared_task:
            raise TypeError(f"Can't re-decorate a celery task {func.__name__} with {self}")

    def __str__(self):
        if self.retry_on_lambda is _never_retry:
            _rol = "None"
        elif callable(self.retry_on_lambda):
            _rol = self.retry_on_lambda.__name__
        else:
            _rol = "None"
        return (
            f"SharedTask("
            f"atomic={self.atomic},"
            f"commit_on_errors={self.commit_on_errors},"
            f"retry_on_errors={self.retry_on_errors},"
            f"retry_on_lambda={_rol},"
            f"retry_countdown={self.retry_countdown},"
            f"bind={self.bind},"
            f"celery_kwargs={self.celery_kwargs},"
            f")"
        )


def extended_shared_task(
    func: Callable = None,
    *,
    atomic=False,
    commit_on_errors: Exceptions = tuple(),
    max_retries: Union[NotSet, int] = not_set,
    retry_on_errors: Exceptions = tuple(),
    retry_on_lambda: Callable[[Exception], bool] = _never_retry,
    retry_countdown: int = FIVE_MINUTES,
    bind: bool = False,
    **celery_kwargs,
) -> Callable:
    """
    Wrapper over SharedTask to allow using it with or without arguments. See `SharedTask` for further info about arguments.
    """
    if callable(func):
        return SharedTask().decorate(func)
    else:
        return SharedTask(
            atomic=atomic,
            commit_on_errors=commit_on_errors,
            max_retries=max_retries,
            retry_on_errors=retry_on_errors,
            retry_on_lambda=retry_on_lambda,
            retry_countdown=retry_countdown,
            bind=bind,
            **celery_kwargs,
        )

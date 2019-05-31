# -*- coding: utf-8 -*-
try:
    from mcod.celeryapp import app as celery_app

    __all__ = ['celery_app']
except ImportError:
    pass

version = '1.5.0'

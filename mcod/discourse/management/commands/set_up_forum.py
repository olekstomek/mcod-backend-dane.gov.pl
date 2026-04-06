import argparse
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from mcod.discourse.manager import DiscourseManager

logger = logging.getLogger("mcod")


class Command(BaseCommand):
    setup_steps = [
        "create_admin_api_key",
        "setup_settings",
        "sync_users",
        "setup_default_theme",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--show-all",
            default=False,
            action="store_true",
            help="show skipped settings",
        )
        parser.add_argument(
            "--host",
            type=str,
            default=settings.DISCOURSE_HOST,
            help="Discourse host",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="Discourse admin username",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Discourse admin password",
        )
        parser.add_argument(
            "--theme_path",
            type=str,
            help="Path to zip file with discourse theme which will be uploaded and set as forum default theme.",
        )
        parser.add_argument(
            "--file",
            metavar="filename",
            type=argparse.FileType("r"),
            help="read config from json file",
        )
        parser.add_argument(
            dest="keyval",
            nargs="*",
            metavar="KEY=VALUE",
            help="Add key[=[value]] settings. May appear multiple times.",
        )
        parser.add_argument(
            "--step_name",
            "--step-name",
            type=str,
            help="Choose single step forum setup",
            choices=self.setup_steps,
        )

    def handle(self, *args, **options):
        logger.info("Forum site-settings")
        logger.debug(options)

        manager_kwargs = {}
        if options.get("host"):
            manager_kwargs["host"] = options.pop("host")
        forum_manager = DiscourseManager(**manager_kwargs)
        single_step = options.get("step_name", "")
        if single_step:
            getattr(forum_manager, single_step)(**options)
        else:
            logger.info("Performing full forum setup.")
            for step in self.setup_steps:
                getattr(forum_manager, step)(**options)

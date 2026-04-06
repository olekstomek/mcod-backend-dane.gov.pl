import logging
from argparse import ArgumentParser
from pathlib import Path

import certifi
from django.core.management import BaseCommand

logger = logging.getLogger("mcod")


class Command(BaseCommand):
    """
    Custom Django management command to retrieve a nginx certificate
    and add it to the certifi library.
    """

    help = "Gets nginx certificate and imports it to certifi library."

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "nginx_cert_path",
            type=Path,
            default=Path("configs/nginx/certs/mcod.local.pem"),
            nargs="?",
            help="Certificate used by the nginx container for SSL.",
        )

    def handle(self, *args, **options) -> None:
        """Handle method to execute the selected command."""
        logger.debug("Started configuring certifi..")
        nginx_cert_path = options["nginx_cert_path"]
        certi_file: str = certifi.where()

        with open(nginx_cert_path, "r") as nginx_cert, open(certi_file, "a") as certi_pem:  # noqa: 501
            certi_pem.write(nginx_cert.read())
            logger.info("Certi file updated successfully.")

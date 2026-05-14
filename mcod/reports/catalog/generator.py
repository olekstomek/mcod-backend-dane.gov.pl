import csv
import io
import logging
import zipfile
from contextlib import ExitStack
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, TextIO

from dateutil.relativedelta import relativedelta
from django.conf import settings
from more_itertools import ichunked

from .provider import CatalogDataProvider

logger = logging.getLogger("mcod")

_LANGUAGES = ["pl", "en"]


class CsvReportDialect(csv.excel):
    delimiter = ";"


def _build_file_paths(language: str) -> Dict[str, Path]:
    today: date = datetime.today().date()
    previous_day: date = today - relativedelta(days=1)

    lang_dir = Path(settings.METADATA_MEDIA_ROOT) / language
    return {
        "lang_dir": lang_dir,
        # CSV paths
        "new_file": lang_dir / f"katalog_{today.isoformat()}.csv",
        "previous_file": lang_dir / f"katalog_{previous_day.isoformat()}.csv",
        "symlink": lang_dir / "katalog.csv",
        # ZIP paths
        "new_zip_file": lang_dir / f"katalog_{today.isoformat()}.zip",
        "symlink_zip": lang_dir / "katalog.zip",
    }


def _manage_files(paths: Dict[str, Dict[str, Path]]) -> None:
    for lang_paths in paths.values():
        previous_file: Path = lang_paths["previous_file"]
        new_file: Path = lang_paths["new_file"]
        symlink_file: Path = lang_paths["symlink"]

        if previous_file.exists():
            previous_file.unlink()

        if new_file.exists():
            if symlink_file.exists() or symlink_file.is_symlink():
                symlink_file.unlink()
            symlink_file.symlink_to(new_file)


def _manage_zip_files(paths: Dict[str, Dict[str, Path]]) -> None:
    for lang_paths in paths.values():
        # ZIP cleanup
        new_zip: Path = lang_paths["new_zip_file"]
        lang_dir: Path = lang_paths["lang_dir"]

        # Remove ANY existing zip files that are not the one we just created
        # This handles cases where reports were skipped for several days
        for existing_zip in lang_dir.glob("katalog_*.zip"):
            if existing_zip.is_file() and existing_zip != new_zip:
                try:
                    existing_zip.unlink()
                    logger.info(f"Removed old ZIP archive: {existing_zip}")
                except OSError as e:
                    logger.error(f"Failed to remove {existing_zip}: {e}")

        # Update ZIP symlink
        symlink_zip: Path = lang_paths["symlink_zip"]
        if new_zip.exists():
            symlink_zip.unlink(missing_ok=True)
            symlink_zip.symlink_to(new_zip)


def create_chunked_zip(source_csv: Path, target_zip: Path, rows_per_chunk: int) -> None:
    """
    Streams chunks from an existing CSV file directly into a new ZIP archive.

    Args:
        source_csv: Path to the original, large CSV file.
        target_zip: Path where the resulting ZIP archive will be saved.
        rows_per_chunk: Maximum number of data rows per CSV chunk inside the ZIP.
    """
    with open(source_csv, "r", encoding="utf-8", newline="") as f_in:
        reader = csv.reader(f_in, dialect=CsvReportDialect)

        header = next(reader, None)
        if header is None:
            logger.warning(f"CSV chunk header not found in {source_csv}")
            return

        with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for chunk_idx, chunk_iterator in enumerate(ichunked(reader, rows_per_chunk), 1):
                chunk_filename = f"katalog_{chunk_idx}.csv"

                with zf.open(chunk_filename, "w") as buffer:
                    with io.TextIOWrapper(buffer, encoding="utf-8", newline="") as text_writer:
                        writer = csv.writer(text_writer, dialect=CsvReportDialect)
                        writer.writerow(header)
                        for row in chunk_iterator:
                            writer.writerow(row)


def generate_catalog_csv_report() -> None:
    paths: Dict[str, Dict[str, Path]] = {lang: _build_file_paths(lang) for lang in _LANGUAGES}
    for lang in _LANGUAGES:
        paths[lang]["lang_dir"].mkdir(parents=True, exist_ok=True)

    chunk_size: int = settings.CATALOG_REPORT_CHUNK_SIZE
    provider = CatalogDataProvider(_LANGUAGES, chunk_size=chunk_size)
    writers: Dict[str, csv.writer] = {}
    with ExitStack() as stack:
        headers: Dict[str, List[str]] = provider.get_headers()
        for lang in _LANGUAGES:
            file: TextIO = stack.enter_context(open(paths[lang]["new_file"], "w", newline=""))
            writer = csv.writer(file, dialect=CsvReportDialect)
            writers[lang] = writer
            writers[lang].writerow(headers[lang])

        for row in provider:
            for lang in _LANGUAGES:
                writers[lang].writerow(row.get_for_language(lang))

    _manage_files(paths)

    # Process generated CSVs into chunked ZIPs
    max_zip_rows: int = settings.CSV_CATALOG_REPORT_MAX_ROWS_PER_FILE
    for lang in _LANGUAGES:
        create_chunked_zip(
            source_csv=paths[lang]["new_file"],
            target_zip=paths[lang]["new_zip_file"],
            rows_per_chunk=max_zip_rows,
        )

    _manage_zip_files(paths)

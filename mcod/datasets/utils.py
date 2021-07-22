from mcod import settings


def _batch_qs(qs):
    batch_size = settings.CSV_CATALOG_BATCH_SIZE
    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield start, end, total, qs[start:end]

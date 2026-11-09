# seo/fallback.py
"""Page-time reads of the seo tables with a safety net for a deploy where the code is
already live but `migrate` has not created seo_pageseo / seo_faqitem yet.

The deploy order stays: migrate first, restart after (docs/DEPLOY_CHECKLIST.md).
"""

import logging
from contextlib import nullcontext

from django.db import connection, transaction
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


def read(query, default):
    """Return query() (evaluate it inside: list(), .first()). If the database refuses it
    (ProgrammingError / OperationalError, e.g. a missing seo table), log one warning and
    return `default`, the same as "no row". Nothing is cached here; any other error is
    raised as usual.

    Inside an open transaction (ATOMIC_REQUESTS, tests) the query runs in a savepoint, so a
    failure does not abort that transaction. In autocommit (production: no ATOMIC_REQUESTS)
    there is no transaction to protect, so no BEGIN/COMMIT is added to the page."""
    try:
        with transaction.atomic() if connection.in_atomic_block else nullcontext():
            return query()
    except (ProgrammingError, OperationalError) as exc:
        logger.warning("seo tables not readable (is `migrate seo` applied?), template defaults used: %s",
                       str(exc).splitlines()[0])
        return default

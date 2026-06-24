"""
krs/tasks.py

CELERY_BEAT_SCHEDULE örneği (settings.py):

    # Günlük: her gün çalışır, o günün vadeli sözleşmelerini işler
    "run-krs-pipeline-daily": {
        "task": "krs.tasks.run_krs_pipeline_task",
        "schedule": crontab(minute=30, hour="5"),
        "args": [2],
        "kwargs": {"mod": "daily"},
    },

    # Aylık: ayın son günü tam BDDK bildirimi için
    "run-krs-pipeline-monthly": {
        "task": "krs.tasks.run_krs_pipeline_task",
        "schedule": crontab(minute=0, hour="6", day_of_month="last"),
        "args": [2],
        "kwargs": {"mod": "monthly"},
    },
"""

from __future__ import annotations
from datetime import date
from typing import Optional
from celery import shared_task
from .services.pipeline import run_krs_pipeline


@shared_task(name="krs.tasks.run_krs_pipeline_task")
def run_krs_pipeline_task(
    company_id: int,
    rapor_tarihi: Optional[str] = None,
    mod: str = "daily",
) -> str:
    """
    rapor_tarihi : "YYYY-MM-DD" string veya None (bugün).
    mod          : "daily" (günlük, varsayılan) veya "monthly" (aylık).
    """
    parsed = date.fromisoformat(rapor_tarihi) if rapor_tarihi else None
    count = run_krs_pipeline(company_id, parsed, mod=mod)
    return f"{count} sözleşme için KRS hesaplandı (company={company_id}, mod={mod})."

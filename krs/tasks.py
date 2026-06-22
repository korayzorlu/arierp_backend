"""
krs/tasks.py

Mevcut common.tasks.fetch_data_from_leaseflex vb. ile aynı stilde tanımlı
Celery task. CELERY_BEAT_SCHEDULE'a eklemek için settings.py'nizdeki ilgili
dict'e şunu ekleyebilirsiniz (Otomatik_Kapama'nın orijinalde gece/sabah
saatlerinde tetiklendiğini gözlemlediğimiz için örnek olarak sabah 05:30
verildi, kendi ihtiyacınıza göre değiştirin):

    "run-krs-pipeline-task": {
        "task": "krs.tasks.run_krs_pipeline_task",
        "schedule": crontab(minute=30, hour="5"),
        "args": [2],
    },
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from celery import shared_task

from .services.pipeline import run_krs_pipeline


@shared_task(name="krs.tasks.run_krs_pipeline_task")
def run_krs_pipeline_task(company_id: int, rapor_tarihi: Optional[str] = None) -> str:
    """
    rapor_tarihi: "YYYY-MM-DD" formatında string, verilmezse bugünün
    tarihi kullanılır (None Celery args üzerinden JSON-serileştirilebilir
    olması için string olarak alınıyor).
    """
    parsed = date.fromisoformat(rapor_tarihi) if rapor_tarihi else None
    count = run_krs_pipeline(company_id, parsed)
    return f"{count} sözleşme için KRS hesaplandı (company={company_id})."

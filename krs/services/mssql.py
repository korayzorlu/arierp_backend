"""
krs/services/mssql.py

Leasflex (MSSQL) bağlantısı için yardımcı fonksiyon. Mevcut
`fetch_partners_from_leaseflex` deseninizle aynı stili kullanır:
ayrı bir .sql dosyasından sorguyu okuyup pyodbc ile çalıştırır.
"""

from __future__ import annotations

import os
from typing import Iterator

import pyodbc
from django.conf import settings


def _load_sql(filename: str) -> str:
    sql_path = os.path.join(settings.BASE_DIR, "krs", "sql", filename)
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def fetch_kapama_hareketleri() -> Iterator[dict]:
    """
    Program.cs / TEMERRUT_OLUSTUR bloğundaki MSSQL sorgusunun birebir
    portunu çalıştırır. Sözleşme (ContractHeaderId) + tarih bazında fatura/
    ödeme/protokol toplamlarını döner.

    Sonuçlar ContractHeaderId, Tarih sırasına göre gelir (bkz. sql dosyasının
    sonundaki ORDER BY) - pipeline.py bu sıralamaya güvenerek itertools.groupby
    ile sözleşme bazlı gruplama yapar.

    NOT: Bu sorgu, FIFO eşleştirmesi için bir sözleşmenin TÜM geçmişine
    aynı anda ihtiyaç duyduğundan, mevcut `fetch_partners_from_leaseflex`
    deseninizdeki gibi sabit boyutlu (BATCH_SIZE) parçalar halinde
    fetchmany() ile işlenmiyor; cursor.fetchall() ile tek seferde belleğe
    alınıyor. Veri hacmi çok büyürse (yüz binlerce satır), bu fonksiyonu
    `yield`leyen bir generator'a çevirip pipeline.py'de
    itertools.groupby'ı doğrudan cursor üzerinde çalıştırabilirsiniz; mevcut
    hacimde (aktif sözleşme sayısı x ortalama hareket sayısı) bunun gerekli
    olması beklenmez.
    """
    conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)
    try:
        cursor = conn.cursor()
        cursor.execute(_load_sql("kapama_hareketleri.sql"))
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
    finally:
        conn.close()

    for row in rows:
        yield dict(zip(columns, row))

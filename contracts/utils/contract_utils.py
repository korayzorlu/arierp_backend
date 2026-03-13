from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings

import pyodbc
import os

from datetime import datetime
import pandas as pd
import io
import os
import random
import string
import gc

from contracts.models import *
from leasing.models import Lease
from common.models import Status
from partners.models import Partner
from common.utils.common_utils import normalize,safe_decimal

def import_contracts(self, df_json):
    df = pd.read_json(io.StringIO(df_json), orient='records')
    
    required_columns = []
    empty_rows = df[required_columns].isnull().any(axis=1)
    if empty_rows.any():
        self.process.status = "rejected"
        self.process.save()
        self.process.delete()
        return

    self.process.status = "in_progress"
    self.process.items_count = len(df)
    self.process.save()
    
    previous_progress = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        #type_list = [item.strip().lower() for item in row["type"].split(",")]

        if Contract.objects.filter(code = row["Sözleşme Kodu"]).exists():
            continue

        if row['KOFtan Sözleşmeye Aktarım Tar.']:
            kof_tan_sozlesmeye_aktarim_tarihi = datetime.fromtimestamp(row['KOFtan Sözleşmeye Aktarım Tar.'] / 1000)
        else:
            kof_tan_sozlesmeye_aktarim_tarihi = None

        if row['LopOpenDate']:
            lop_open_date = datetime.fromtimestamp(row['LopOpenDate'] / 1000)
        else:
            lop_open_date = None
        
        obj = Contract.objects.create(
            company = self.user.user_companies.filter(is_active=True).first().company,
            code = row['Sözleşme Kodu'],
            #partner = None,
            kof = row['KOF No'],
            quotation = row['Teklif No'],
            committe = row['Komite Adı'],
            credit_type = row['Kredi Tipi Adı'],
            customer_representative = row['Müş. Temsilcisi'],
            supplier = row['Satıcı'],
            project = row['Proje'],
            status = Status.objects.filter(name = row["Alt Statü"]).first() or None,
            mkk_tesciline_gonderilecek_mi = True if row['MKK Tesciline Gönderilecek Mi ?'] == "True" else False,
            kof_tan_sozlesmeye_aktarim_tarihi = make_aware(kof_tan_sozlesmeye_aktarim_tarihi),
            lop_open_date = make_aware(lop_open_date),
        )
        obj.save()

    self.process.progress = 100
    self.process.status = "completed"
    self.process.save()

def export_contract_payments(self):
    objs = ContractPayment.objects.select_related("contract","contract__partner").filter(
        Q(contract__project = "SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        Q(contract__vendor__crm_code = "11802")
    ).order_by("-contract__code","-date")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme": [],
        "Proje": [],
        "Nereden": [],
        "Nereye": [],
        "İşlem Tİpi": [],
        "İşlem Grubu": [],
        "Hesap Kart Kodu": [],
        "Cari Kart Adı": [],
        "İşlem Tarihi": [],
        "Borç": [],
        "Alacak": [],
        "PB": [],
        "Yerel Borç": [],
        "Yerel Alacak": [],
        "Kur(Yerel)": [],
        "Açıklama": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress


        data["Sözleşme"].append(obj.contract.code)
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Nereden"].append(obj.trn_from_id or "")
        data["Nereye"].append(obj.type or "")
        data["İşlem Tİpi"].append(obj.posting_type or "")
        data["İşlem Grubu"].append(obj.group_name or "")
        data["Hesap Kart Kodu"].append(obj.account_code or "")
        data["Cari Kart Adı"].append(obj.account_name or "")
        data["İşlem Tarihi"].append(obj.date or "")
        data["Borç"].append(obj.debit_amount)
        data["Alacak"].append(obj.credit_amount)
        data["PB"].append(obj.currency.code if obj.currency else "")
        data["Yerel Borç"].append(obj.local_debit_amount)
        data["Yerel Alacak"].append(obj.local_credit_amount)
        data["Kur(Yerel)"].append(obj.exchange_rate)
        data["Açıklama"].append(obj.description)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Borç",
        "Alacak",
        "Yerel Borç",
        "Yerel Alacak",
        "Kur(Yerel)",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "contracts", "contract_payments", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-tahsilatlar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)

            # Workbook'u al
            workbook = writer.book
            worksheet = writer.sheets['Sayfa']

            # Kolon isimlerine göre format uygula
            for idx, col in enumerate(df.columns, 1):  # enumerate 1'den başlıyor
                if col in numeric_columns:
                    for cell in worksheet.iter_cols(min_col=idx, max_col=idx, min_row=2):
                        for c in cell:
                            c.number_format = '#,##0.00'   # İstediğin format
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def fetch_contracts_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "contracts","sql","sozlesmeler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        contracts = Contract.objects.select_related("status","company","quotation_obj","partner").filter(company__id=int(company))
        statuses = Status.objects.select_related().all()
        partners = Partner.objects.select_related().filter(company__id=int(company))
        quotations = Quotation.objects.select_related().filter(company__id=int(company))
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_by_code = {c.contract_id: c for c in contracts if c.contract_id}
        del contracts
        gc.collect()

        statuses_dict = {s.name: s for s in statuses}
        partners_dict = {p.crm_code: p for p in partners}
        quotations_dict = {q.code: q for q in quotations}
        currencies_dict = {c.code: c for c in currencies}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.ContractHeaderId):
                    obj = (contract_by_code.get(str(data.ContractHeaderId)))
                else:
                    obj = None

                if obj:
                    obj.contract_id = str(data.ContractHeaderId) or ""
                    obj.code = str(data.ContractHeaderCode) or ""
                    obj.partner = partners_dict.get(str(data.CustomerId))
                    obj.quotation_obj = quotations_dict.get(str(data.QuotationHeaderId))
                    obj.vendor = partners_dict.get(str(data.VendorId))
                    obj.committe = str(data.CommitteeName) or ""
                    obj.credit_type = str(data.CreditTypeName) or ""
                    obj.customer_representative = str(data.CustomerRepresentative) or ""
                    obj.supplier = data.Vendor or ""
                    obj.project = data.Project or ""
                    # obj.status = statuses_dict.get(normalize(data["SubStatuteName"]))
                    obj.status = statuses_dict.get(str(data.SubStatuteName))
                    obj.lop_open_date = make_aware(data.LopOpenDate) if data.LopOpenDate else None
                    obj.created_date_leaseflex = make_aware(data.CreatedDate) if data.CreatedDate else None
                    obj.currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Contract(
                        company = company_obj,
                        contract_id = str(data.ContractHeaderId) or "",
                        code = str(data.ContractHeaderCode) or "",
                        partner = partners_dict.get(str(data.CustomerId)),
                        quotation_obj = quotations_dict.get(str(data.QuotationHeaderId)),
                        vendor = partners_dict.get(str(data.VendorId)),
                        committe = str(data.CommitteeName) or "",
                        credit_type = str(data.CreditTypeName) or "",
                        customer_representative = str(data.CustomerRepresentative) or "",
                        supplier = data.Vendor or "",
                        project = data.Project or "",
                        status = statuses_dict.get(str(data.SubStatuteName)),
                        lop_open_date = make_aware(data.LopOpenDate) if data.LopOpenDate else None,
                        created_date_leaseflex = make_aware(data.CreatedDate) if data.CreatedDate else None,
                        currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    ))
                    create_progress += 1
            if update_objs:
                Contract.objects.bulk_update(update_objs, [
                    "contract_id",
                    "code",
                    "partner",
                    "quotation_obj",
                    "vendor",
                    "committe",
                    "credit_type",
                    "customer_representative",
                    "supplier",
                    "project",
                    "status",
                    "lop_open_date",
                    "created_date_leaseflex",
                    "currency",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Contract.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        del contract_by_code
        gc.collect()
        print(f"Toplam {update_progress} sözleşme güncellendi.")
        print(f"Toplam {create_progress} sözleşme oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)


def fetch_contract_payments_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "contracts","sql","tahsilatlar.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        currencies_dict = {c.code: c for c in currencies}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            # 1. codes
            contract_payment_codes = [r.TrnId for r in records]
            contract_codes = [r.TrnOprContractId for r in records]
            # 2. querysets
            contract_payments = ContractPayment.objects.select_related().filter(trn_id__in=contract_payment_codes)
            contracts = Contract.objects.select_related().filter(contract_id__in=contract_codes)
            # 3. dicts
            contract_payment_dict = {cp.trn_id: cp for cp in contract_payments}
            contracts_dict = {c.contract_id: c for c in contracts}
            for index,data in enumerate(records):
                if str(data.TrnId):
                    obj = (contract_payment_dict.get(str(data.TrnId)))
                else:
                    obj = None

                if obj:
                    obj.contract = contracts_dict.get(str(data.TrnOprContractId))
                    obj.trn_id = str(data.TrnId) or ""
                    obj.trn_from_id = str(data.TrnFromId) or ""
                    obj.ledger_account_id = str(data.TrnFromLedgerAccountId_AC) or ""
                    obj.ledger_account_name = str(data.TrnFromLedgerAccountId_AN) or ""
                    obj.trade_account_code = str(data.TrnFromTradeAccountCode) or ""
                    obj.type = str(data.viewTrnFromToType) or ""
                    obj.source_type = str(data.TrnSourceType) or ""
                    obj.posting_type = str(data.viewTrnPostingType) or ""
                    obj.group_name = str(data.JrnStpPstGrpName) or ""
                    obj.account_code = str(data.TrnAccountCode) or ""
                    obj.account_name = str(data.AccName) or ""
                    obj.date = data.TrnDate.date() if data.TrnDate else None
                    obj.due_date = data.TrnDueDate.date() if data.TrnDueDate else None
                    obj.debit_amount = safe_decimal(data.TrnAmountTypeDebit)
                    obj.credit_amount = safe_decimal(data.TrnAmountTypeCredit)
                    obj.local_debit_amount = safe_decimal(data.TrnAmountTypeLocalDebit)
                    obj.local_credit_amount = safe_decimal(data.TrnAmountTypeLocalCredit)
                    obj.currency = currencies_dict.get("TRY" if data.TrnCurrencyCode == "TL" else data.TrnCurrencyCode)
                    obj.exchange_rate = safe_decimal(data.TrnExchangeRateLocal)
                    obj.description = str(data.TrnDescription) or ""
                    obj.user_name = str(data.CreatedUserId) or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    if data.TrnOprContractId and contracts_dict.get(str(data.TrnOprContractId)):
                        create_objs.append(ContractPayment(
                            company = company_obj,
                            contract = contracts_dict.get(str(data.TrnOprContractId)),
                            trn_id = str(data.TrnId) or "",
                            trn_from_id = str(data.TrnFromId) or "",
                            ledger_account_id = str(data.TrnFromLedgerAccountId_AC) or "",
                            ledger_account_name = str(data.TrnFromLedgerAccountId_AN) or "",
                            trade_account_code = str(data.TrnFromTradeAccountCode) or "",
                            type = str(data.viewTrnFromToType) or "",
                            source_type = str(data.TrnSourceType) or "",
                            posting_type = str(data.viewTrnPostingType) or "",
                            group_name = str(data.JrnStpPstGrpName) or "",
                            account_code = str(data.TrnAccountCode) or "",
                            account_name = str(data.AccName) or "",
                            date = data.TrnDate.date() if data.TrnDate else None,
                            due_date = data.TrnDueDate.date() if data.TrnDueDate else None,
                            debit_amount = safe_decimal(data.TrnAmountTypeDebit),
                            credit_amount = safe_decimal(data.TrnAmountTypeCredit),
                            local_debit_amount = safe_decimal(data.TrnAmountTypeLocalDebit),
                            local_credit_amount = safe_decimal(data.TrnAmountTypeLocalCredit),
                            currency = currencies_dict.get("TRY" if data.TrnCurrencyCode == "TL" else data.TrnCurrencyCode),
                            exchange_rate = safe_decimal(data.TrnExchangeRateLocal),
                            description = str(data.TrnDescription) or "",
                            user_name = str(data.CreatedUserId) or "",
                        ))
                        create_progress += 1
            if update_objs:
                ContractPayment.objects.bulk_update(update_objs, [
                    "contract",
                    "trn_id",
                    "trn_from_id",
                    "ledger_account_id",
                    "ledger_account_name",
                    "trade_account_code",
                    "type",
                    "posting_type",
                    "group_name",
                    "account_code",
                    "account_name",
                    "date",
                    "due_date",
                    "debit_amount",
                    "credit_amount",
                    "local_debit_amount",
                    "local_credit_amount",
                    "currency",
                    "exchange_rate",
                    "description",
                    "user_name",
                    "source_type",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                ContractPayment.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} tahsilat güncellendi.")
        print(f"Toplam {create_progress} tahsilat oluşturuldu.")
        print("--------")      

    except Exception as e:
        print(e)

def fetch_warning_notices_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "contracts","sql","ihtarlar.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        warning_notices = WarningNotice.objects.select_related("company","contract","contract__currency").filter(company__id=int(company))
        warning_notices.delete()
        contracts = Contract.objects.select_related().filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        warning_notice_by_code = {c.document_id: c for c in warning_notices if c.document_id}
        contracts_dict = {c.code: c for c in contracts}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.RiskDocumentId):
                    obj = (warning_notice_by_code.get(str(data.RiskDocumentId)))
                else:
                    obj = None

                if obj:
                    obj.contract = contracts_dict.get(str(data.ContractHeaderId))
                    obj.document_id = str(data.RiskDocumentId) or ""
                    obj.risk_id = str(data.RiskHeaderId) or ""
                    obj.customer_id = str(data.CustomerId) or ""
                    obj.debit_amount = safe_decimal(data.Debit)
                    obj.daily_wages_date = data.DailyWagesDate.date() if data.DailyWagesDate else None
                    obj.process_start_date = data.ProcessStartDate.date() if data.ProcessStartDate else None
                    obj.service_date = data.ServiceDate.date() if data.ServiceDate else None
                    obj.official_cancellation_date = data.OfficialCancellationDate.date() if data.OfficialCancellationDate else None
                    obj.paid = safe_decimal(data.Paid)
                    obj.diff = safe_decimal(data.Diff)
                    obj.state = str(data.State) or ""
                    obj.approval_state = str(data.ApprovalState) or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    if data.ContractHeaderId and contracts_dict.get(str(data.ContractHeaderId)):
                        create_objs.append(WarningNotice(
                            company = company_obj,
                            contract = contracts_dict.get(str(data.ContractHeaderId)),
                            document_id = str(data.RiskDocumentId) or "",
                            risk_id = str(data.RiskHeaderId) or "",
                            customer_id = str(data.CustomerId) or "",
                            debit_amount = safe_decimal(data.Debit),
                            daily_wages_date = data.DailyWagesDate.date() if data.DailyWagesDate else None,
                            process_start_date = data.ProcessStartDate.date() if data.ProcessStartDate else None,
                            service_date = data.ServiceDate.date() if data.ServiceDate else None,
                            official_cancellation_date = data.OfficialCancellationDate.date() if data.OfficialCancellationDate else None,
                            paid = safe_decimal(data.Paid),
                            diff = safe_decimal(data.Diff),
                            state = str(data.State) or "",
                            approval_state = str(data.ApprovalState) or "",
                        ))
                        create_progress += 1
            if update_objs:
                WarningNotice.objects.bulk_update(update_objs, [
                    "contract",
                    "document_id",
                    "risk_id",
                    "customer_id",
                    "debit_amount",
                    "daily_wages_date",
                    "process_start_date",
                    "service_date",
                    "official_cancellation_date",
                    "paid",
                    "diff",
                    "state",
                    "approval_state",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                WarningNotice.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        
        wns = WarningNotice.objects.select_related("contract").filter(company__id=int(company))
        cwns = ComprehensiveWarningNotice.objects.select_related("contract").filter(company__id=int(company))
        for wn in wns:
            if wn.contract.contract_comprehensive_warning_notices.all().exists():
                cwn=wn.contract.contract_comprehensive_warning_notices.all().first()
                cwn.service_date=wn.service_date
                cwn.official_cancellation_date=wn.official_cancellation_date
                cwn.save()

        for cwn in cwns:
            if not cwn.contract.contract_warning_notices.all().exists():
                lease = Lease.objects.select_related("contract").filter(contract = cwn.contract).first()
                if lease:
                    lease.warning_notice_status = "ihtar_yok"
                    lease.save()
                cwn.delete()

        print(f"Toplam {update_progress} ihtar güncellendi.")
        print(f"Toplam {create_progress} ihtar oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
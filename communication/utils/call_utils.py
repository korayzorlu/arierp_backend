from django.conf import settings
from django.db.models.functions import Replace
from django.db.models import F, Value
from django.utils.timezone import make_aware

import requests
import os
from datetime import datetime, timedelta

from partners.models import Partner
from communication.models import Call

def parse_date(date_str):
    if not date_str:
        return date_str
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str
    
def parse_dt(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return make_aware(datetime.strptime(value, fmt))
        except ValueError:
            continue
    return None

def ms_to_hhmmss(ms):
    seconds = ms // 1000
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def fetch_calls_with_voyce(params):
    url = "https://integration-voyce.voyce.arileasing.com.tr/integration-voyce/v1/CdrDetails"

    headers = {
        "Authorization": "sk-v1-jVGfakpqhzF7VGpcgW6N9",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    payload = {
        "StartTime": f"{parse_date(params.get('start_date'))}T08:00:00Z",
        "EndTime": f"{parse_date(params.get('end_date'))}T18:00:00Z",
    }

    ca_path = os.path.join(settings.BASE_DIR, "VOYCE_CA.crt")

    response = requests.post(url, headers=headers, json=payload, verify=ca_path)
    
    if response.status_code == 200 and response.json():
        data_list = response.json()
        for data in data_list:
            partner = Partner.objects.filter().annotate(
                fixed_phone_number=Replace(
                    Replace(
                        Replace(
                            Replace(F("phone_number"), Value(" "), Value("")),
                            Value("-"), Value("")
                        ),
                        Value("("), Value("")
                    ),
                    Value(")"), Value("")
                )
            ).filter(fixed_phone_number=data.get("RemoteNumber")).first()

            if partner:
                if Call.objects.filter(
                    company=partner.company,
                    partner=partner,
                    queue=data.get("Queue"),
                    phone_number=data.get("RemoteNumber"),
                    start_time=parse_dt(data.get("StartTime")),
                    end_time=parse_dt(data.get("EndTime")),
                ).exists():
                    continue 
                
                Call.objects.create(
                    company=partner.company,
                    partner=partner,
                    queue=data.get("Queue"),
                    agent=data.get("Agent"),
                    direction=data.get("Direction"),
                    phone_number=data.get("RemoteNumber"),
                    start_time=parse_dt(data.get("StartTime")),
                    end_time=parse_dt(data.get("EndTime")),
                    connected_length=timedelta(milliseconds=int(data.get("ConnectedLength"))) if data.get("ConnectedLength") else None,
                    disposition=data.get("Disposition"),
                    verdict=data.get("Verdict"),
                )


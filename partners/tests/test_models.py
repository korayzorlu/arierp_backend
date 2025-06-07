import pytest
from django.contrib.auth import get_user_model

import json

from partners.models import Partner
from companies.models import Company,UserCompany
from common.models import Country, City

User = get_user_model()

@pytest.mark.django_db
def test_add_partner_view(client):
    # Kullanıcı ve şirket oluştur
    user = User.objects.create_user(username="testuser", password="testpass")
    company = Company.objects.create(name="Test Company")
    active_company = UserCompany.objects.create(is_active = True, company = company,user=user)

    # Gerekli ülke/şehir vs. objelerini oluştur
    country = Country.objects.create(name="Turkey", iso2="TR")
    city = City.objects.create(name="Istanbul", country=country)

    # Kullanıcı girişini yap
    client.force_login(user)

    # Gönderilecek veri
    data = {
        "companyId": company.id,
        "customer": True,
        "name": "Test Partner",
        "formalName": "Test Ltd.",
        "vatOffice": "Kadıköy",
        "vatNo": "1234567890",
        "country": "TR",
        "city": {"id": city.id},
        "address": "Adres 1",
        "address2": "Adres 2",
        "isBillingSame": True,
        "billingCountry": "TR",
        "billingCity": {"id": city.id},
        "billingAddress": "Fatura Adresi 1",
        "billingAddress2": "Fatura Adresi 2",
        "phoneCountry": "TR",
        "phoneNumber": "+905551112233",
        "email": "test@example.com",
        "web": "https://example.com",
        "about": "Test açıklama"
    }

    # View URL'ini belirt (senin urls.py yapına göre ayarla)
    response = client.post("/api/partners/add_partner/", data=json.dumps(data), content_type="application/json")

    print(response.status_code)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["status"] == "success"
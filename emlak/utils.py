import requests

def fetch_real_estate_agent(company):
    url = "https://www.sahibinden.com/ilan/emlak-konut-satilik-remax-ani-dan-site-icerisinde-sehir-manzarali-satilik-1-plus1-daire-1329471024/detay"

    response = requests.get(url)
    print(response)
    if response.status_code == 200:
        data = response.json()
        # Process the data as needed
        print(data)
import requests

url = 'https://v6.exchangerate-api.com/v6/125568a3b90c116da3e43a7a/latest/USD'

response = requests.get(url)
data = response.json()

print(data)
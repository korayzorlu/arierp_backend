from django.contrib.gis.geoip2 import GeoIP2

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_client_country(ip):
    g = GeoIP2()
    try:
        country = g.country(ip)['country_code']
    except Exception as e:
        country = None
    return country
from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings
import ldap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def fetch_ldap_user_info(username):
    try:
        ldap_server = settings.AUTH_LDAP_SERVER_URI
        bind_dn = settings.AUTH_LDAP_BIND_DN
        bind_password = settings.AUTH_LDAP_BIND_PASSWORD

        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(bind_dn, bind_password)
        search_base = "OU=ARI,DC=arileasing,DC=local"
        search_filter = f"(sAMAccountName={username})"
        result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
        # result okunabilir şekilde yazdırılır

        return result

        for dn, attrs in result:
            print(f"Distinguished Name: {dn}")
            for key, value in attrs.items():
                # bytes tipini decode et, liste ise virgülle ayır
                decoded = []
                for v in value:
                    if isinstance(v, bytes):
                        try:
                            decoded.append(v.decode("utf-8"))
                        except Exception:
                            decoded.append(str(v))
                    else:
                        decoded.append(str(v))
                print(f"  {key}: {', '.join(decoded)}")
                print("-" * 60)
        conn.unbind_s()
    except Exception as e:
        logging.error(f"LDAP user info error: {e}")
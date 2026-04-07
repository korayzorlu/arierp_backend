from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings
import ldap
import logging
import traceback

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

def fetch_ldap_all_users_info():
    try:
        ldap_server = settings.AUTH_LDAP_SERVER_URI
        bind_dn = settings.AUTH_LDAP_BIND_DN
        bind_password = settings.AUTH_LDAP_BIND_PASSWORD

        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(bind_dn, bind_password)
        search_base = "OU=ARI,DC=arileasing,DC=local"
        # Kullanabileceğiniz bazı LDAP filtre örnekleri:
        # "(objectClass=user)"            -> Tüm kullanıcı nesneleri
        # "(objectClass=person)"          -> Tüm person nesneleri
        # "(sAMAccountName=*)"            -> sAMAccountName alanı olan tüm nesneler
        # "(mail=*)"                      -> E-posta adresi olan kullanıcılar
        # "(department=IT)"               -> Departmanı IT olan kullanıcılar
        # "(memberOf=CN=GroupName,OU=Groups,DC=arileasing,DC=local)" -> Belirli bir gruba üye olanlar
        # "(|(objectClass=user)(objectClass=group))" -> Kullanıcı ve grup nesneleri
        # "(&(objectClass=user)(department=Sales))"  -> Departmanı Sales olan kullanıcılar

        search_filter = "(objectClass=department)"  # Tüm kullanıcıları getirir
        result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
        return result
    except Exception as e:
        logging.error(f"LDAP user info error: {e}")

def fetch_ldap_departments_info():
    try:
        ldap_server = settings.AUTH_LDAP_SERVER_URI
        bind_dn = settings.AUTH_LDAP_BIND_DN
        bind_password = settings.AUTH_LDAP_BIND_PASSWORD

        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(bind_dn, bind_password)
        search_base = "OU=ARI,DC=arileasing,DC=local"
        search_filter = "(department=*)"
        result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)
        departments = set()
        for dn, attrs in result:
            dept = attrs.get('department')
            if dept:
                # department genellikle bytes tipinde olur
                for d in dept:
                    if isinstance(d, bytes):
                        departments.add(d.decode('utf-8'))
                    else:
                        departments.add(str(d))
        return list(departments)
    except Exception as e:
        logging.error(f"LDAP user info error: {e}")

def get_ldap_user_department(username):
    try:
        data = fetch_ldap_user_info(username)
        if data and len(data) > 0:
            department_value = data[0][1]["department"][0]
            position_value = data[0][1]["title"][0]
            if isinstance(department_value, bytes):
                department_value = department_value.decode("utf-8")
                position_value = position_value.decode("utf-8")
            return {"department": department_value, "position": position_value}
    except Exception as e:
        print(e)
        traceback.print_exc()

def get_ldap_user_position(username):
    try:
        data = fetch_ldap_user_info(username)
        if data and len(data) > 0:
            position_value = data[0][1]["title"][0]
            if isinstance(position_value, bytes):
                position_value = position_value.decode("utf-8")
            return position_value
    except Exception as e:
        print(e)
        traceback.print_exc()

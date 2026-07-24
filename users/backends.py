from django_auth_ldap.backend import LDAPBackend


class CustomLDAPBackend(LDAPBackend):
    """LDAP ile doğrulanan kullanıcının şifresini hash'leyerek yerel DB'ye de yazar.

    django-auth-ldap varsayılan olarak LDAP kullanıcısının şifresini yerelde
    saklamaz (password alanı boş kalır, admin'de "No password set." görünür).
    Burada başarılı LDAP doğrulamasından sonra düz metin şifre set_password()
    ile hash'lenip kaydedilir; böylece LDAP sunucusuna erişilemediği
    durumlarda ModelBackend fallback'i de çalışabilir.
    """

    def authenticate_ldap_user(self, ldap_user, password):
        user = super().authenticate_ldap_user(ldap_user, password)

        if user is not None and password:
            user.set_password(password)
            user.save(update_fields=["password"])

        return user

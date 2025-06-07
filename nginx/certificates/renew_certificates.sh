#!/bin/bash

# Log dosyasını tanımla
LOGFILE="/home/admin/marswide/marswide_backend/nginx/certificates/renew.log"

# Certbot yenileme komutunu çalıştır
docker run --rm \
  -v "/home/admin/marswide/marswide_backend/nginx/certbot-www:/var/www/certbot" \
  -v "/home/admin/marswide/marswide_backend/nginx/certificates:/etc/letsencrypt" \
  certbot/certbot renew --webroot --webroot-path=/var/www/certbot > "$LOGFILE" 2>&1

# Log dosyasını kontrol et
if grep -q "Congratulations, all renewals succeeded" "$LOGFILE" || grep -q "new certificate deployed" "$LOGFILE"; then
    echo "Sertifikalar yenilendi. NGINX yeniden başlatılıyor..."
    docker restart nginx
else
    echo "Sertifikalar zaten güncel. NGINX yeniden başlatılmadı."
fi
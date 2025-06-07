<p align="center">
	<img src=https://micho-app.com/static/images/landing/esms-logo-red-light.daa1f270c395.png width=138/>
</p>
<h1 align="center">KZ TOOLKIT</h1>

## <img src=https://git-scm.com/images/logos/downloads/Git-Icon-1788C.png width=20/> Git

### Token

- Git auth token for sync.
```

```

### Configure

- Kullanıcı bilgilerini sisteme işlemek.
```sh
git config --global user.name "****"
git config --global user.email "****"
```

### New Repo

- Yeni proje için yeni repo oluşturmak için github üzerinde yeni repo oluştur ve terminale dön. 
```sh
git init
git add .
git commit -m "First commit"
git remote add origin https://github.com/kullaniciadi/repoadi.git
git push -u origin master
```

### SSH Auth

- SSH key dosyaları konumuna gitmek.
```sh
cd /.ssh/
```

- SSH key oluşturmak.
```sh
# git hesabı email adresini gir
ssh-keygen -t rsa -C "your_email@example.com"
```

- SSH keyi yazdırmak ve kopyalamak.
```sh
cat id_rsa.pub
```

- Bu adımdan sonra Github hesabına tarayıcıda git ve account settings alanında SSH keys içerisine girip yeni SSH key oluştura gidip bu key'i yapıştır ve kaydet.

- SSH ajanını kullanmak.
```sh
eval "$(ssh-agent -s)"
```

- Keyi SSH ajanına eklemek.
```sh
ssh-add ~/.ssh/id_ed25519
```

- Bu adımdan sonra git reponun bağlı olduğu proje konumuna git.

- Bağlı olunan repoyu kontrol etmek.
```sh
git remote -v
```

- Bağlı olunan repo url'ini düzeltmek.
```sh
git remote set-url origin git@github.com:username/repo.git
```


## <img src=https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Ubuntu-logo-no-wordmark-2022.svg/1200px-Ubuntu-logo-no-wordmark-2022.svg.png width=20/> Ubuntu

### Workspace

- Proje konumuna gider ve virtualenv'i başlatır.
```sh
cd projects/django/michoapp/ && source myenv/bin/activate && cd michoapp/
```
### Memory Control

- Önbellek temizlemek.
```sh 
sudo sysctl -w vm.drop_caches=3
```

### Disk Control

- Tüm disklerin boyutunu kontrol etmek.
```sh
df -h
```

- içinde bulunulan klasördeki dosyaların boyutunu kontrol etmek.
```sh
sudo du -bsh *
```

- Disk alanı genişletmekle ilgili bilgiler; [ChatGPT](https://chatgpt.com/c/66f67f21-2e4c-8002-bfc7-22f738f8651e)


### Dosya Sıkıştırma

- Bir dosyayı sıkıştırmak.
```sh
tar -czvf arsiv-ismi.tar.gz arsivlenecek-dosya-ismi-ya-da-klasor
```

- Sıkıştırılan bir dosyayı çıkartmak.
```sh
# bulunulan konuma çıkacaksa
tar -xzvf arsiv-ismi.tar.gz

# başka bir konuma çıkacaksa
tar -xzvf arsiv-ismi.tar.gz -C /hedef/klasor
```

### Dosya transferi
- SSH ile karşıya dosya göndermek.
```sh
scp /yerel/dosya kullanici_adi@hedef_ip:/hedef/klasor
```

- SSH ile karşıdan dosya almak.
```sh
# bulunulan konuma gelecekse
scp kullanici_adi@hedef_ip:/hedef/dosya .

# başka bir konuma gelecekse
scp kullanici_adi@hedef_ip:/hedef/dosya /yerel/konum
```
## <img src=https://cdn4.iconfinder.com/data/icons/logos-and-brands/512/97_Docker_logo_logos-512.png width=20/> Docker

### Dockerfile

- Bir servis için konteyner oluşturmak istendiğinde bu dosya oluşturulur.
```sh
# Dockerfile
# Django için dockerfile örneği

# Base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the project files
COPY . /app/

# Run django project
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Expose the port
EXPOSE 8000
```

### Image

- İmaj oluşturulmak istendiğinde bu dosya oluşturulur.
```sh
# docker-compose.yml
# Django projesi için imaj örneği

version: '3'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app

```

```sh
# docker-compose-override.yml
# Localde çalıştırmak için ayrı dosya oluşturup docker-compose.yml ile bağlantılı çalıştırılır

services:
  web:
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      DJANGO_SETTINGS_MODULE: dockertest.settings
```

```sh
# docker-compose-prod.yml
# Production ortamında çalıştırmak için ayrı dosya oluşturup docker-compose.yml ile bağlantılı çalıştırılır

services:
  web:
    #command: gunicorn dockertest.wsgi:application --bind 0.0.0.0:8000
    #command: gunicorn --access-logfile - --workers 33 --limit-request-line 6000 --bind unix:/run/gunicorn.sock core.asgi:application -k uvicorn.workers.UvicornWorker
    command: gunicorn --access-logfile - --workers 33 --limit-request-line 6000 --bind 0.0.0.0:8000 dockertest.wsgi:application
    environment:
      DJANGO_SETTINGS_MODULE: dockertest.settings
```

### Build

- Docker ile build, sadece ilgili dockerfile dosyasını build eder.
```sh
docker build -t your_image_name .

# eski verileri temizlemek için
docker build --no-cache -t your_image_name .
```

- Docker-compose ile build, hem dockerfile hem de yml dosyalarını build eder.
```sh
# Tek servis için imaj oluşturmak istenirse
docker-compose build servis_adi

# Tüm servisler için imaj oluşturmak istenirse
docker-compose build

# eski verileri temizlemek için
docker-compose build --no-cache
```

### Run

- Çalışan dosyayı durdurmak.
```sh
docker-compose -f docker-compose.yml down
```

- Dosyayı çalıştırmak.
```sh
# terminalde anlık çıktıları görmek için
docker-compose -f docker-compose.yml up

# terminalde çıktı görmeden arka planda çalıştırmak için
docker-compose -f docker-compose.yml up -d

# full komut
docker-compose down && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

- Log izlemek
```sh
docker-compose logs -f
```

- Bir konteynerdaki uygulama için bir komut çalıştmak gerekirse.
```sh
# burada web konteyner ismini temsil eder başka bir şey de olabilir.
docker-compose exec web python manage.py makemigration
```

### Network

- Network oluşturmak.
```sh
docker network create shared_network
```

- Konteynerleri network'e bağlamak.
```sh
#docker-compose.yml

#herhangi bir konteyner olabilir web burada sadece bir örnek.
services:
  web:
    .
    .
    .
    networks: shared_network
networks:
  shared_network:
    external: true
```

## <img src=https://www.postgresql.org/media/img/about/press/elephant.png width=20/> Postgresql

### Join postgres

- Postgres konsoluna erişmek.
```sh
sudo -u postgres psql
```

### Backup & Restore

- Backup dosyası oluştumak.
```sh
sudo pg_dump -f "dump_file.sql" -h "<db_host_name>" -U <db_username> "<database_name>"
```
- Bu adımdan itibaren makemigrations ve migrate işlemi yapılmamalı. Yeni ve eski db'ler arasında kesinlikle migration farkı olmamalı.

- Backup dosyasını üzerine işleyeceğimiz yeni ve temiz db oluşturmak.
```sql
CREATE DATABASE new_db_name;
```

- Owner değiştirmek
```postgres
GRANT ALL PRIVILEGES ON DATABASE myproject TO myprojectuser;
ALTER DATABASE name OWNER TO new_owner;
```

- Restore işlemi.
```sh
sudo psql --dbname="<new_database_name>" -h "new_database_host_name" -U "new_db_username" -f dump_file.sql
```

## <img src=https://code.visualstudio.com/assets/images/code-stable.png width=20/> VS Code

### Markdown

- Önizleme modunda çift tıklama ile oluşan eylemi kapatmak.
```
markdown.preview.doubleClickToSwitchToEditor
```

## <img src=https://static-00.iconduck.com/assets.00/website-icon-2048x2048-ax2y60lj.png width=20/> Yardımcı Kaynaklar

### Django

- Nginx ve Gunicorn ile Ubuntu'da Django projesi kurulumu; [Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)

## <img src=https://desktop.docker.com/extensions/nginx_docker-extension/raw_githubusercontent_com/nginx/docker-extension/main/logo.svg width=20/> Nginx

### Conf

- conf dosyasını yapılandırmak.
```sh
# nginx.conf

server {
    server_name example.com www.example.com;

    proxy_buffer_size 128k;
    proxy_buffers 4 256k;
    proxy_busy_buffers_size 256k;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /staticfiles/;
    }

    location /media/ {
        root /;
    }

    location /.well-known/acme-challenge/ {
        root /staticfiles; # Certbot'un doğrulama dosyalarını yerleştirdiği dizin
    }

    location / {
        proxy_pass http://web:8000;  # Django uygulamasına yönlendir
        #proxy_pass http://188.132.143.226:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

    }


    client_max_body_size 10M;

}

server {
    listen 80;
    server_name example.com www.example.com;

    if ($host = example.com) {
        return 301 https://$host$request_uri;
    }

    if ($host = www.example.com) {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    #ssl_certificate /etc/ssl/certs/fullchain.pem;
    #ssl_certificate_key /etc/ssl/certs/privkey.pem;

    location / {
        proxy_pass http://example_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    client_max_body_size 10M;
}

```

## <img src=https://certbot.eff.org/assets/certbot-logo-1A-6d3526936bd519275528105555f03904956c040da2be6ee981ef4777389a4cd2.svg width=20/> Certbot

### Certificate

- Sertifika almak.
```sh
sudo certbot --nginx -d example.com -d www.example.com
```

## Düzenlenecek
```
WHERE cha_evrak_tip = 0 OR cha_evrak_tip = 63

koray.zorlu@entechsemar.local
zLL%&867383

raid 0 hız
raid 1 güvenlik
raid 5 hız + güvenlik

eSmR56782hgh87632

8jpmno7u7m44q6i1g8ql177838tr9wez

0 11 * * * /bin/systemctl restart postgresql
30 12 * * * /bin/systemctl restart postgresql
30 14 * * * /bin/systemctl restart postgresql
30 15 * * * /bin/systemctl restart postgresql
30 16 * * * /bin/systemctl restart postgresql
30 17 * * * /bin/systemctl restart postgresql
00 18 * * * /bin/systemctl restart postgresql
```
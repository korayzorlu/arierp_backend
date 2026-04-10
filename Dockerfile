# Base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    apt-transport-https \
    ca-certificates
#RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN apt-get update && apt-get install -y gnupg curl
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null

RUN curl -sSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
    -o /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi-dev
#oracle
RUN apt-get update && apt-get install -y libaio1t64 wget unzip && \
    ln -sf /usr/lib/x86_64-linux-gnu/libaio.so.1t64 /usr/lib/x86_64-linux-gnu/libaio.so.1 && \
    mkdir -p /opt/oracle && \
    wget -q https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linuxx64.zip \
         -O /tmp/instantclient.zip && \
    unzip /tmp/instantclient.zip -d /opt/oracle/ && \
    rm /tmp/instantclient.zip

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_26:$LD_LIBRARY_PATH
#oracle-end
ENV PATH="$PATH:/opt/mssql-tools18/bin"
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
#RUN pip freeze > requirements.txt
#RUN pip install gunicorn

# Copy the project files
COPY . /app/

# Run django project
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Expose the port
EXPOSE 8000
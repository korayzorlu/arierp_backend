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
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl -sSL https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
    -o /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*
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
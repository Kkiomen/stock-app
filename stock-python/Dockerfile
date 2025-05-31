FROM python:3.10-slim

WORKDIR /app

# Zainstaluj wymagane pakiety systemowe
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Skopiuj pliki requirements
COPY requirements.txt ./

# Zainstaluj zależności Python
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj wszystkie pliki aplikacji
COPY . .

# Utwórz katalog cache
RUN mkdir -p /app/cache

# Expose port dla FastAPI
EXPOSE 8000

# Uruchom FastAPI server
CMD ["python", "app.py"]

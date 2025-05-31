#FROM python:3.10-slim
#
## Instalacja zależności systemowych
#RUN apt-get update && \
#    apt-get install -y cron && \
#    apt-get clean
#
## Instalacja zależności Pythona
#COPY requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt
#
## Ustawienie katalogu roboczego
#WORKDIR /app
#
## Skopiowanie skryptów
#COPY stock_model.py run-cron.sh crontab.txt ./
#
## Ustawienie uprawnień
#RUN chmod +x run-cron.sh && crontab crontab.txt
#
## Start crona w trybie foreground
#CMD ["cron", "-f"]



FROM python:3.10-slim

WORKDIR /app

COPY stock_model.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "stock_model.py"]
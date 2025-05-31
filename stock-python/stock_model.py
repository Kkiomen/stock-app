# %% --------------------------------------------------------------------------
# 1. IMPORTY & PARAMETRY
# -----------------------------------------------------------------------------
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from pytrends.request import TrendReq
import os
import requests
import json
import io
import base64
import uuid

TICKER          = "BTC-USD"
START_DATE      = "2017-01-01"      # pełna historia ~2014, ale 2017+ jest „czystrza”
TEST_SIZE_PCT   = 0.15              # ostatnie ~15 % na test
FORECAST_DAYS   = 20                # prognoza na 2 tygodnie

uuid = str(uuid.uuid4())

# --------------------------------------------
# 1. Pobranie BTC bez MultiIndex w indeksie
# --------------------------------------------
raw = yf.download(
        TICKER,
        start=START_DATE,
        auto_adjust=False,
        progress=False
)

def send_stock_data_to_api(raw: pd.DataFrame, api_url: str = "http://laravel.test/api/stock-api") -> requests.Response | None:
    """
    Przesyła dane giełdowe do API jako JSON.

    Parametry:
    - raw: oryginalny DataFrame z danymi z yfinance
    - api_url: adres API, do którego wysyłane są dane

    Zwraca:
    - obiekt Response z `requests.post` lub None w przypadku błędu
    """
    try:
        raw_copy = raw.copy()

        # Upewnij się, że kolumny są typu string
        if isinstance(raw_copy.columns, pd.MultiIndex):
            raw_copy.columns = ['_'.join(map(str, col)).strip() for col in raw_copy.columns]
        else:
            raw_copy.columns = [str(col) for col in raw_copy.columns]

        # Konwersja do listy rekordów
        raw_json_records = raw_copy.reset_index().to_dict(orient='records')

        # Payload do API
        payload = {
            "ticker": TICKER,
            "uuid": uuid,
            "stock_data": raw_json_records
        }

        # Wysłanie żądania POST
        response = requests.post(
            url=api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, default=str),
            timeout=10
        )

        return response

    except Exception as e:
        print(f"❌ Błąd podczas wysyłania danych do API: {e}")
        return None

response = send_stock_data_to_api(raw)

if response and response.ok:
    print("✅ Dane zostały wysłane poprawnie.")
elif response:
    print(f"❌ Błąd API: {response.status_code} – {response.text}")
else:
    print("❌ Nie udało się wysłać danych – brak odpowiedzi.")

# ► jeśli przyjdzie MultiIndex: pole nazwy = 0, ticker = 1
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)   # <-- najbezpieczniej

# teraz wiemy, że mamy zwykłe 'Close', 'Volume', ...
btc = raw[['Close', 'Volume']].copy()
btc.columns = ['close', 'volume']                   # zamieniamy na lower-case
btc.index = btc.index.tz_localize(None)


# --------------------------------------------
# 2. Google Trends
# --------------------------------------------
trends_filename = f"google_trends_{TICKER.replace('-', '_')}.csv"

gt = None
use_trends = False

try:
    pytrends = TrendReq(hl='en-US', tz=360, requests_args={'headers': {'User-Agent': 'Mozilla/5.0'}})
    pytrends.build_payload(['bitcoin'], timeframe=f'{START_DATE} {datetime.today():%Y-%m-%d}')
    gt = (pytrends.interest_over_time()
            .rename(columns={'bitcoin': 'gt_bitcoin'})
            .drop(columns=['isPartial'])
            .resample('D').ffill())
    gt.index = pd.to_datetime(gt.index).tz_localize(None)

    gt.to_csv(trends_filename)  # ✅ zapis do pliku
    print(f"✅ Dane Google Trends zapisane do pliku: {trends_filename}")
    use_trends = True

except Exception as e:
    print(f"❌ Błąd podczas pobierania Google Trends: {e}")

    # Próba wczytania z pliku, jeśli istnieje
    if os.path.exists(trends_filename):
        try:
            gt = pd.read_csv(trends_filename, index_col=0, parse_dates=True)
            print(f"📂 Wczytano dane Google Trends z pliku: {trends_filename}")
            use_trends = True
        except Exception as e_file:
            print(f"❌ Błąd przy wczytywaniu pliku z Google Trends: {e_file}")
    else:
        print("ℹ️ Brak pliku z danymi Google Trends – pomijam ten wskaźnik.")

# --------------------------------------------
# 3. Łączenie – concat z warunkiem
# --------------------------------------------
if use_trends:
    btc = pd.concat([btc, gt], axis=1).ffill()
else:
    btc['gt_bitcoin'] = np.nan  # zachowujemy strukturę kolumn

# %% --------------------------------------------------------------------------
# 4. FEATURE ENGINEERING
# -----------------------------------------------------------------------------
def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # log-zwroty
    out['ret_1']  = np.log(out['close']).diff()
    out['ret_7']  = np.log(out['close']).diff(7)
    out['ret_30'] = np.log(out['close']).diff(30)

    # momentum indicators
    rsi = RSIIndicator(out['close'], window=14)
    out['rsi_14'] = rsi.rsi()

    macd = MACD(out['close'])
    out['macd'] = macd.macd()
    out['macd_signal'] = macd.macd_signal()

    # volatility
    boll = BollingerBands(out['close'])
    out['bb_high'] = boll.bollinger_hband()
    out['bb_low']  = boll.bollinger_lband()
    out['bb_width'] = (out['bb_high'] - out['bb_low']) / out['close']

    # wolumen – z-score
    out['vol_z'] = (out['volume'] - out['volume'].rolling(30).mean()) / out['volume'].rolling(30).std()

    # Google Trends – 7-dniowa średnia
    out['gt_7d'] = out['gt_bitcoin'].rolling(7).mean()

    # target = jutrzejszy log-zwrot
    out['target'] = out['ret_1'].shift(-1)

    return out.dropna()

data = make_features(btc)

# %% --------------------------------------------------------------------------
# 5. TRAIN / TEST SPLIT (time-series aware)
# -----------------------------------------------------------------------------
split_idx = int(len(data) * (1 - TEST_SIZE_PCT))
train = data.iloc[:split_idx]
test  = data.iloc[split_idx:]

X_train, y_train = train.drop(columns=['target']), train['target']
X_test,  y_test  = test.drop(columns=['target']),  test['target']

# %% --------------------------------------------------------------------------
# 6. MODEL XGBOOST
# -----------------------------------------------------------------------------
model = XGBRegressor(
    n_estimators=600,
    learning_rate=0.03,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='reg:squarederror',
    random_state=42
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae  = mean_absolute_error(y_test, y_pred)
print(f"Test MAE  : {mae:.5f}")
print(f"Test RMSE : {rmse:.5f}")

# %% --------------------------------------------------------------------------
# 7. ODTWORZENIE POZIOMU CENY NA OKRESIE TESTOWYM
# -----------------------------------------------------------------------------
test_prices = btc.loc[X_test.index, 'close']
# kumulujemy przewidziane log-zwroty
pred_price = test_prices.shift(1) * np.exp(y_pred)   # because price_t = price_{t-1} * e^{ret}

# %% --------------------------------------------------------------------------
# 8. FORECAST NA KOLEJNE DNI
# -----------------------------------------------------------------------------
last_prices = btc.copy()
future_dates = pd.bdate_range(last_prices.index[-1] + pd.Timedelta(days=1), periods=FORECAST_DAYS)

for d in future_dates:
    # dodaj puste NaN – potrzebne do rollingów
    last_prices.loc[d] = np.nan
    feat = make_features(last_prices).iloc[[-1]].drop(columns=['target'])
    next_ret = model.predict(feat)[0]
    next_price = last_prices.iloc[-2]['close'] * np.exp(next_ret)
    last_prices.at[d, 'close'] = next_price
    last_prices.at[d, 'volume'] = last_prices.iloc[-2]['volume']   # placeholder
    last_prices.at[d, 'gt_bitcoin'] = last_prices.iloc[-2]['gt_bitcoin']  # placeholder

forecast = last_prices.loc[future_dates, ['close']].rename(columns={'close':'forecast_close'})

# %% --------------------------------------------------------------------------
# 9. WYKRES
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(btc.index[-500:], btc['close'][-500:], label="Kurs rzeczywisty")
ax.plot(pred_price.index, pred_price, label="Prognoza (okres testowy)", color='orange')
ax.plot(forecast.index, forecast['forecast_close'], label=f"Forecast +{FORECAST_DAYS} d", color='red')
ax.set_title(TICKER + " – model XGBoost (log-returns → price)")
ax.set_xlabel("Data")
ax.set_ylabel("Cena [USD]")
ax.legend()
fig.tight_layout()

# Zapisz do bufora jako PNG
buf = io.BytesIO()
fig.savefig(buf, format='png')
plt.close(fig)  # zamknij fig, żeby nie pokazywać
buf.seek(0)


# Zamień na base64
img_base64 = base64.b64encode(buf.read()).decode('utf-8')

# Payload do API
payload = {
    "ticker": TICKER,
    "uuid": uuid,
    "image": img_base64
}

# Wysłanie żądania POST
response = requests.post(
    url="http://laravel.test/api/stock-api/image",
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload, default=str),
    timeout=10
)

# Zapisz do bufora jako PNG
buf = io.BytesIO()
fig.savefig(buf, format='png')
plt.close(fig)  # zamknij fig, żeby nie pokazywać
buf.seek(0)


# %% --------------------------------------------------------------------------
# 10. TABELA WYNIKÓW
# -----------------------------------------------------------------------------
results = pd.DataFrame({
    'Date'            : forecast.index,
    'Forecast_Close'  : forecast['forecast_close'].round(2)
}).set_index('Date')

def send_forecast_to_api(forecast_df: pd.DataFrame, api_url: str = "http://laravel.test/api/stock-api/forecast") -> requests.Response | None:
    """
    Wysyła dane prognozy do API jako JSON.

    Parametry:
    - forecast_df: DataFrame z prognozą (data jako indeks, 'forecast_close' jako kolumna)
    - api_url: adres API

    Zwraca:
    - obiekt Response lub None w przypadku błędu
    """
    try:
        forecast_payload = {
            "ticker": TICKER,
            "uuid": uuid,
            "forecast": forecast_df.reset_index().to_dict(orient='records')
        }

        response = requests.post(
            url=api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(forecast_payload, default=str),
            timeout=10
        )
        return response
    except Exception as e:
        print(f"❌ Błąd podczas wysyłania prognozy do API: {e}")
        return None

print("\nPrognoza na kolejne dni:")
print(results)


response = send_forecast_to_api(forecast)

if response and response.ok:
    print("✅ Prognoza została wysłana poprawnie.")
elif response:
    print(f"❌ Błąd API podczas wysyłania prognozy: {response.status_code} – {response.text}")
else:
    print("❌ Nie udało się wysłać prognozy – brak odpowiedzi.")










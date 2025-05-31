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
import argparse
import sys

# Parsowanie argumentów z linii komend
def parse_arguments():
    parser = argparse.ArgumentParser(description='Stock Analysis with XGBoost')
    parser.add_argument('--ticker', type=str, default='BTC-USD', help='Stock ticker symbol')
    parser.add_argument('--trends', type=str, default=None, help='Google trends tag')
    parser.add_argument('--start_date', type=str, default='2017-01-01', help='Start date for analysis')
    parser.add_argument('--test_size_pct', type=float, default=0.15, help='Test size percentage')
    parser.add_argument('--forecast_days', type=int, default=20, help='Number of forecast days')

    return parser.parse_args()

# Parsuj argumenty
args = parse_arguments()

TICKER = args.ticker
GOOGLE_TRENDS_KEY = args.trends
START_DATE = args.start_date
TEST_SIZE_PCT = args.test_size_pct
FORECAST_DAYS = args.forecast_days

# Generuj UUID dla tej sesji
uuid_session = str(uuid.uuid4())

print(f"🚀 Rozpoczynam analizę dla {TICKER}")
print(f"📈 Google Trends: {GOOGLE_TRENDS_KEY}")
print(f"📅 Data rozpoczęcia: {START_DATE}")
print(f"📊 Procent testu: {TEST_SIZE_PCT}")
print(f"🔮 Dni prognozy: {FORECAST_DAYS}")
print(f"🆔 UUID sesji: {uuid_session}")

# --------------------------------------------
# 1. Pobranie danych bez MultiIndex
# --------------------------------------------
try:
    raw = yf.download(
        TICKER,
        start=START_DATE,
        auto_adjust=False,
        progress=False
    )
    print(f"✅ Pobrano {len(raw)} dni danych dla {TICKER}")
except Exception as e:
    print(f"❌ Błąd pobierania danych: {e}")
    sys.exit(1)

def send_stock_data_to_api(raw: pd.DataFrame, api_url: str = "http://laravel.test/api/stock-api") -> requests.Response | None:
    """
    Przesyła dane giełdowe do API jako JSON.
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
            "uuid": uuid_session,
            "parameters": {
                "start_date": START_DATE,
                "test_size_pct": TEST_SIZE_PCT,
                "forecast_days": FORECAST_DAYS
            },
            "stock_data": raw_json_records
        }

        # Wysłanie żądania POST
        response = requests.post(
            url=api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, default=str),
            timeout=30
        )
        return response
    except Exception as e:
        print(f"❌ Błąd podczas wysyłania danych do API: {e}")
        return None

# Wyślij dane do API
response = send_stock_data_to_api(raw)
if response and response.ok:
    print("✅ Dane zostały wysłane poprawnie do Laravel API.")
elif response:
    print(f"❌ Błąd API: {response.status_code} – {response.text}")
else:
    print("❌ Nie udało się wysłać danych – brak odpowiedzi.")

# ► jeśli przyjdzie MultiIndex: pole nazwy = 0, ticker = 1
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = raw.columns.get_level_values(0)

# teraz wiemy, że mamy zwykłe 'Close', 'Volume', ...
btc = raw[['Close', 'Volume']].copy()
btc.columns = ['close', 'volume']
btc.index = btc.index.tz_localize(None)

# --------------------------------------------
# 2. Google Trends
# --------------------------------------------
trends_filename = f"google_trends_{TICKER.replace('-', '_')}.csv"
gt = None
use_trends = False

try:
    pytrends = TrendReq(hl='en-US', tz=360, requests_args={'headers': {'User-Agent': 'Mozilla/5.0'}})
    search_term = (GOOGLE_TRENDS_KEY if GOOGLE_TRENDS_KEY is not None
                   else 'bitcoin' if 'BTC' in TICKER.upper()
                   else TICKER.split('-')[0].lower())
    pytrends.build_payload([search_term], timeframe=f'{START_DATE} {datetime.today():%Y-%m-%d}')

    gt = (pytrends.interest_over_time()
            .rename(columns={search_term: f'gt_{search_term}'})
            .drop(columns=['isPartial'])
            .resample('D').ffill())
    gt.index = pd.to_datetime(gt.index).tz_localize(None)
    gt.to_csv(trends_filename)
    print(f"✅ Dane Google Trends zapisane do pliku: {trends_filename} dla '{search_term}'")
    use_trends = True
except Exception as e:
    print(f"❌ Błąd podczas pobierania Google Trends: {e}")
    # Próba wczytania z pliku
    if os.path.exists(trends_filename):
        try:
            gt = pd.read_csv(trends_filename, index_col=0, parse_dates=True)
            print(f"📂 Wczytano dane Google Trends z pliku: {trends_filename}")
            use_trends = True
        except Exception as e_file:
            print(f"❌ Błąd przy wczytywaniu pliku z Google Trends: {e_file}")

# --------------------------------------------
# 3. Łączenie danych
# --------------------------------------------
if use_trends:
    btc = pd.concat([btc, gt], axis=1).ffill()
else:
    btc[f'gt_{TICKER.split("-")[0].lower()}'] = np.nan

# %% --------------------------------------------------------------------------
# 4. FEATURE ENGINEERING
# -----------------------------------------------------------------------------
def make_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # log-zwroty
    out['ret_1'] = np.log(out['close']).diff()
    out['ret_7'] = np.log(out['close']).diff(7)
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
    out['bb_low'] = boll.bollinger_lband()
    out['bb_width'] = (out['bb_high'] - out['bb_low']) / out['close']

    # wolumen – z-score
    out['vol_z'] = (out['volume'] - out['volume'].rolling(30).mean()) / out['volume'].rolling(30).std()

    # Google Trends – 7-dniowa średnia
    trends_col = [col for col in out.columns if col.startswith('gt_')]
    if trends_col:
        out['gt_7d'] = out[trends_col[0]].rolling(7).mean()

    # target = jutrzejszy log-zwrot
    out['target'] = out['ret_1'].shift(-1)

    return out.dropna()

print("🔧 Tworzenie cech technicznych...")
data = make_features(btc)
print(f"✅ Utworzono {len(data)} rekordów z cechami")

# %% --------------------------------------------------------------------------
# 5. TRAIN / TEST SPLIT
# -----------------------------------------------------------------------------
split_idx = int(len(data) * (1 - TEST_SIZE_PCT))
train = data.iloc[:split_idx]
test = data.iloc[split_idx:]

X_train, y_train = train.drop(columns=['target']), train['target']
X_test, y_test = test.drop(columns=['target']), test['target']

print(f"📊 Dane treningowe: {len(X_train)} rekordów")
print(f"📊 Dane testowe: {len(X_test)} rekordów")

# %% --------------------------------------------------------------------------
# 6. MODEL XGBOOST
# -----------------------------------------------------------------------------
print("🤖 Trenowanie modelu XGBoost...")
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
mae = mean_absolute_error(y_test, y_pred)

print(f"✅ Model wytrenowany!")
print(f"📈 Test MAE: {mae:.5f}")
print(f"📈 Test RMSE: {rmse:.5f}")

# %% --------------------------------------------------------------------------
# 7. FORECAST NA KOLEJNE DNI
# -----------------------------------------------------------------------------
print(f"🔮 Generowanie prognozy na {FORECAST_DAYS} dni...")

last_prices = btc.copy()
future_dates = pd.bdate_range(last_prices.index[-1] + pd.Timedelta(days=1), periods=FORECAST_DAYS)

for d in future_dates:
    # dodaj puste NaN
    last_prices.loc[d] = np.nan
    feat = make_features(last_prices).iloc[[-1]].drop(columns=['target'])
    next_ret = model.predict(feat)[0]
    next_price = last_prices.iloc[-2]['close'] * np.exp(next_ret)
    last_prices.at[d, 'close'] = next_price
    last_prices.at[d, 'volume'] = last_prices.iloc[-2]['volume']

    # Google Trends placeholder
    trends_col = [col for col in last_prices.columns if col.startswith('gt_')]
    if trends_col:
        last_prices.at[d, trends_col[0]] = last_prices.iloc[-2][trends_col[0]]

forecast = last_prices.loc[future_dates, ['close']].rename(columns={'close': 'forecast_close'})

# %% --------------------------------------------------------------------------
# 8. WYKRES
# -----------------------------------------------------------------------------
print("📊 Generowanie wykresu...")
fig, ax = plt.subplots(figsize=(12, 6))

# Odtworzenie cen na okresie testowym
test_prices = btc.loc[X_test.index, 'close']
pred_price = test_prices.shift(1) * np.exp(y_pred)

ax.plot(btc.index[-500:], btc['close'][-500:], label="Kurs rzeczywisty", linewidth=2)
ax.plot(pred_price.index, pred_price, label="Prognoza (okres testowy)", color='orange', linewidth=2)
ax.plot(forecast.index, forecast['forecast_close'], label=f"Forecast +{FORECAST_DAYS} d", color='red', linewidth=2, linestyle='--')

ax.set_title(f"{TICKER} – model XGBoost (log-returns → price)", fontsize=14)
ax.set_xlabel("Data")
ax.set_ylabel("Cena [USD]")
ax.legend()
ax.grid(True, alpha=0.3)
fig.tight_layout()

# Zapisz do bufora jako PNG
buf = io.BytesIO()
fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
plt.close(fig)
buf.seek(0)

# Zamień na base64
img_base64 = base64.b64encode(buf.read()).decode('utf-8')

# Wyślij wykres do API
payload_image = {
    "ticker": TICKER,
    "uuid": uuid_session,
    "image": img_base64,
    "metrics": {
        "mae": float(mae),
        "rmse": float(rmse),
        "train_size": len(X_train),
        "test_size": len(X_test)
    }
}

try:
    response = requests.post(
        url="http://laravel.test/api/stock-api/image",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload_image, default=str),
        timeout=30
    )
    if response.ok:
        print("✅ Wykres wysłany do API")
    else:
        print(f"❌ Błąd wysyłania wykresu: {response.status_code}")
except Exception as e:
    print(f"❌ Błąd wysyłania wykresu: {e}")

# %% --------------------------------------------------------------------------
# 9. WYSYŁANIE PROGNOZY
# -----------------------------------------------------------------------------
def send_forecast_to_api(forecast_df: pd.DataFrame, api_url: str = "http://laravel.test/api/stock-api/forecast"):
    try:
        forecast_payload = {
            "ticker": TICKER,
            "uuid": uuid_session,
            "forecast_days": FORECAST_DAYS,
            "forecast": forecast_df.reset_index().to_dict(orient='records'),
            "model_metrics": {
                "mae": float(mae),
                "rmse": float(rmse),
                "train_size": len(X_train),
                "test_size": len(X_test)
            }
        }

        response = requests.post(
            url=api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(forecast_payload, default=str),
            timeout=30
        )
        return response
    except Exception as e:
        print(f"❌ Błąd podczas wysyłania prognozy do API: {e}")
        return None

print(f"\n🔮 Prognoza na kolejne {FORECAST_DAYS} dni:")
results = pd.DataFrame({
    'Date': forecast.index,
    'Forecast_Close': forecast['forecast_close'].round(2)
}).set_index('Date')

print(results)

# Wyślij prognozę do API
response = send_forecast_to_api(forecast)
if response and response.ok:
    print("✅ Prognoza została wysłana poprawnie do Laravel API.")
elif response:
    print(f"❌ Błąd API podczas wysyłania prognozy: {response.status_code} – {response.text}")
else:
    print("❌ Nie udało się wysłać prognozy – brak odpowiedzi.")

print(f"\n🎉 Analiza zakończona dla {TICKER}!")
print(f"📊 MAE: {mae:.5f}, RMSE: {rmse:.5f}")
print(f"🆔 UUID sesji: {uuid_session}")

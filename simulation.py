import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pandas as pd
from datetime import datetime

# === EXTERNAL DEPENDENCIES ===
from data_loader import get_data
from indicators import add_indicators
from labeler import create_labels
from model_trainer import train_model
from signal_generator import generate_signal
from visual_reporter import generate_visual_report

def run_simulation(symbol="ETH/USDT"):
    # === Sabitler ===
    TIMEFRAME = "15m"
    FUTURE_PERIOD = 12
    THRESHOLD = 0.005
    PROB_THRESHOLD = 0.55
    DATA_LIMIT = 7000
    INITIAL_BALANCE = 10000
    GITHUB_DIR = "Github"

    log_file = os.path.join(GITHUB_DIR, f"{symbol.replace('/', '_')}_live_log.csv")
    param_file = os.path.join(GITHUB_DIR, f"{symbol.replace('/', '_')}_params.json")
    os.makedirs(GITHUB_DIR, exist_ok=True)

    log_columns = ["Time", "Price", "Action", "Amount", "Balance_After", "Market_Return", "System_Return"]

    # === Önceki Durumu Yükle ===
    if os.path.exists(param_file):
        with open(param_file, "r") as f:
            params = json.load(f)
        position = params.get("position", 0.0)
        entry_price = params.get("entry_price", 0.0)
        balance = params.get("balance", INITIAL_BALANCE)
        market_start_price = params.get("market_start_price", None)
    else:
        position = 0.0
        entry_price = 0.0
        balance = INITIAL_BALANCE
        market_start_price = None

    # === VERİ ÇEKİMİ & ÖZELLİKLER ===
    df = get_data(symbol, TIMEFRAME, total_limit=DATA_LIMIT)
    df = add_indicators(df)
    df = create_labels(df, future_period=FUTURE_PERIOD, threshold=THRESHOLD)
    model, features = train_model(df)

    # === SON BARA GÖRE SİNYAL ===
    df_live = df.iloc[-1:].copy()
    latest_price = df_live["close"].values[0]
    if market_start_price is None:
        market_start_price = latest_price

    signal = generate_signal(df_live, model, features, prob_threshold=PROB_THRESHOLD)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    action = "HOLD"

    if signal == 1 and position == 0:
        position = balance / latest_price
        entry_price = latest_price
        balance = 0.0
        action = "BUY"
    elif signal == 0 and position > 0:
        balance = position * latest_price
        position = 0.0
        entry_price = 0.0
        action = "SELL"

    # === SONUÇLARI HESAPLA ===
    total_balance = balance + position * latest_price
    system_return = (total_balance - INITIAL_BALANCE) / INITIAL_BALANCE
    market_return = (latest_price - market_start_price) / market_start_price

    # === LOG KAYDI ===
    if os.path.exists(log_file):
        df_log = pd.read_csv(log_file)
    else:
        df_log = pd.DataFrame(columns=log_columns)

    df_log.loc[len(df_log)] = [
        now,
        round(latest_price, 2),
        action,
        round(position, 6),
        round(total_balance, 2),
        round(market_return, 4),
        round(system_return, 4)
    ]
    df_log.to_csv(log_file, index=False)

    # === DURUMU JSON'A YAZ ===
    with open(param_file, "w") as f:
        json.dump({
            "symbol": symbol,
            "future_period": FUTURE_PERIOD,
            "threshold": THRESHOLD,
            "prob_threshold": PROB_THRESHOLD,
            "feature_importance": dict(zip(features, model.feature_importances_.tolist())),
            "position": position,
            "entry_price": entry_price,
            "balance": balance,
            "market_start_price": market_start_price
        }, f, indent=2)

    # === DASHBOARD PNG ÜRET ===
    generate_visual_report(symbol)

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

# === COLOR THEMES ===
THEMES = {
    "ETH": {
        "color_model": "#3B82F6",
        "color_market": "#9CA3AF",
        "bg": "#F9FAFB",
        "title": "#1F2937",
        "logo": "Github/assets/eth_logo.png"
    },
    "BTC": {
        "color_model": "#F59E0B",
        "color_market": "#9CA3AF",
        "bg": "#FFFBEB",
        "title": "#78350F",
        "logo": "Github/assets/btc_logo.png"
    }
}

def generate_visual_report(symbol="ETH/USDT"):
    coin = symbol.split("/")[0]
    theme = THEMES.get(coin, THEMES["ETH"])

    GITHUB_DIR = "Github"
    LOG_FILE = os.path.join(GITHUB_DIR, f"{symbol.replace('/', '_')}_live_log.csv")
    PARAM_FILE = os.path.join(GITHUB_DIR, f"{symbol.replace('/', '_')}_params.json")
    OUTPUT_FILE = os.path.join(GITHUB_DIR, "docs", f"{coin}_dashboard.png")  # DOĞRUDAN /docs içine

    # === LOAD DATA ===
    df_log = pd.read_csv(LOG_FILE)
    with open(PARAM_FILE, "r") as f:
        params = json.load(f)

    # === METRICS ===
    total_trades = df_log[df_log["Action"].isin(["BUY", "SELL"])].shape[0] // 2
    cumulative_profit = df_log.iloc[-1]["Balance_After"] - df_log.iloc[0]["Balance_After"]
    profitable_trades = df_log[(df_log["Action"] == "SELL") & (df_log["System_Return"] > df_log["Market_Return"])].shape[0]
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

    # === LAST 5 OUTCOMES ===
    recent = df_log[df_log["Action"] == "SELL"].tail(5)
    recent_results = []
    for _, row in recent.iterrows():
        result = "✅ Win" if row["System_Return"] > row["Market_Return"] else "❌ Loss"
        recent_results.append(f"{row['Time'][-5:]}: {result}")

    # === PLOT ===
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(14, 10), facecolor=theme["bg"])
    gs = fig.add_gridspec(4, 4)

    # === TITLE ===
    ax_title = fig.add_subplot(gs[0, :4])
    ax_title.axis("off")
    ax_title.text(0.01, 0.7, f"{symbol} Strategy Dashboard", fontsize=24, fontweight="bold", color=theme["title"])
    ax_title.text(0.01, 0.3, f"Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", fontsize=14, color="#6B7280")

    # === LOGO ===
    try:
        logo_img = mpimg.imread(theme["logo"])
        imagebox = OffsetImage(logo_img, zoom=0.06)
        ab = AnnotationBbox(imagebox, (0.95, 0.88), frameon=False, xycoords='figure fraction')
        fig.add_artist(ab)
    except Exception as e:
        print(f"⚠️ Logo could not be loaded: {e}")

    # === PERFORMANCE ===
    ax_perf = fig.add_subplot(gs[1, :4])
    ax_perf.plot(df_log["Time"], df_log["System_Return"] * 100, label="Model", color=theme["color_model"], linewidth=2)
    ax_perf.plot(df_log["Time"], df_log["Market_Return"] * 100, label="Market", color=theme["color_market"], linestyle="--")
    ax_perf.set_ylabel("Return (%)", fontsize=12)
    ax_perf.set_title("Performance Comparison", fontsize=16)
    ax_perf.tick_params(axis='x', rotation=45)
    ax_perf.legend(fontsize=10)
    ax_perf.grid(True)

    # === METRICS TEXT ===
    ax_params = fig.add_subplot(gs[2:, 0:2])
    ax_params.axis("off")
    lines = [
        f"Last Action: {df_log.iloc[-1]['Action']}",
        f"Balance: ${df_log.iloc[-1]['Balance_After']:.2f}",
        f"System Return: {df_log.iloc[-1]['System_Return']*100:.2f}%",
        f"Market Return: {df_log.iloc[-1]['Market_Return']*100:.2f}%",
        f"Cumulative Profit: ${cumulative_profit:.2f}",
        f"Total Trades: {total_trades}",
        f"Win Rate: {win_rate:.1f}%",
        "Last 5 Results:"
    ] + recent_results
    for i, line in enumerate(lines):
        ax_params.text(0, 1 - i * 0.08, line, fontsize=12, color="#111827")

    # === FEATURE IMPORTANCE ===
    ax_feat = fig.add_subplot(gs[2:, 2:])
    feat = params["feature_importance"]
    sorted_feat = sorted(feat.items(), key=lambda x: x[1], reverse=True)
    names = [k for k, v in sorted_feat]
    scores = [v for k, v in sorted_feat]
    sns.barplot(x=scores, y=names, ax=ax_feat, color=theme["color_model"])
    ax_feat.set_title("Feature Importance (Current Model)", fontsize=14)
    ax_feat.set_xlim(0, max(scores)*1.2)
    ax_feat.tick_params(labelsize=10)

    # === FOOTER ===
    fig.text(0.5, 0.005, "Powered by BaranTradeAI", ha='center', fontsize=11, color="#6B7280")

    # === SAVE ===
    plt.tight_layout(rect=[0, 0.02, 1, 1])
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    plt.savefig(OUTPUT_FILE)
    plt.close()

# Local test
if __name__ == "__main__":
    generate_visual_report("ETH/USDT")

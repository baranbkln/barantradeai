import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import shutil
import subprocess
from datetime import datetime
from simulation import run_simulation

SYMBOLS = ["ETH/USDT", "BTC/USDT"]
GITHUB_DIR = "Github"
DOCS_DIR = f"docs"

def update_github_pages():
    print("📁 Copying PNGs to GitHub Pages /docs folder...")
    for symbol in SYMBOLS:
        coin = symbol.split("/")[0]
        src = f"{GITHUB_DIR}/{coin}_USDT_dashboard.png"
        dst = f"{DOCS_DIR}/{coin}_dashboard.png"
        try:
            shutil.copy(src, dst)
            print(f"✅ Copied: {src} → {dst}")
        except Exception as e:
            print(f"❌ Error copying {coin}: {e}")

    print("🔁 Committing and pushing to GitHub...")
    subprocess.run(["git", "-C", GITHUB_DIR, "add", "."], check=True)
    subprocess.run([
        "git", "-C", GITHUB_DIR, "commit", "-m",
        f"PNG update: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    ], check=False)
    subprocess.run(["git", "-C", GITHUB_DIR, "push"], check=True)
    print("🚀 GitHub Pages updated.")

def main_loop():
    while True:
        print("\n⏱️ Running simulations...")
        for symbol in SYMBOLS:
            try:
                run_simulation(symbol=symbol)
            except Exception as e:
                print(f"⚠️ Simulation error for {symbol}: {e}")

        update_github_pages()
        print("⏳ Sleeping 15 minutes...\n")
        time.sleep(900)

if __name__ == "__main__":
    main_loop()

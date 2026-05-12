import asyncio, httpx, random, string, os, time
from flask import Flask
from threading import Thread

# --- ⚙️ CONFIG ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1503716739462987821/ZWc2zyrJRVbcgDmRECFfGPxOECYtSdPSZgeGgtNbotbHC3eNbUDKQRK_LZfBo8_KsvTK"
PROXY_URL = "http://iex7l7-country-US:5a4642py@eu.nettify.xyz:8080"

# --- 🛰️ TOKEN LOADER ---
def load_tokens():
    # Priority 1: Check Railway Environment Variable
    env_tokens = os.getenv("TOKENS", "")
    if env_tokens:
        return [t.strip() for t in env_tokens.split(",") if t.strip()]
    
    # Priority 2: Check local file (if uploaded via Railway CLI)
    if os.path.exists("tokens.txt"):
        with open("tokens.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    
    return []

TOKENS = load_tokens()

# --- 🛰️ RAILWAY KEEP-ALIVE ---
app = Flask(__name__)
@app.route('/')
def home(): 
    return f"Sniper Status: {'ACTIVE' if TOKENS else 'WAITING FOR TOKENS'}"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 🚀 THE SNIPER ENGINE ---
async def worker(client, token_queue):
    while True:
        name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
        token = await token_queue.get()
        try:
            r = await client.post(
                "https://discord.com/api/v9/users/@me/pomelo-attempt",
                json={"username": name},
                headers={"Authorization": token}
            )
            if r.status_code == 200 and not r.json().get("taken"):
                # HIT! Send to Webhook
                await client.post(WEBHOOK_URL, json={"content": f"🎯 **HIT:** `{name}`"})
            elif r.status_code == 429:
                await asyncio.sleep(20) 
        except: pass
        token_queue.put_nowait(token)
        await asyncio.sleep(0.3)

async def main():
    if not TOKENS:
        print("❌ No tokens found! Add them to Railway Variables.")
        return
        
    token_queue = asyncio.Queue()
    for t in TOKENS: token_queue.put_nowait(t)
    Thread(target=run_web, daemon=True).start()
    
    async with httpx.AsyncClient(http2=True, proxy=PROXY_URL) as client:
        tasks = [worker(client, token_queue) for _ in range(min(len(TOKENS), 20))]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

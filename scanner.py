import time, math, requests, threading
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests_cache import CachedSession

from config import (
    INTERVAL_FAST, INTERVAL_SLOW, LIMIT,
    MAX_24H_QUOTE_VOL, MIN_PRICE, EXCLUDE_CONTAINS,
    USE_COINGECKO, CG_MAX_MCAP_USD, CG_VS_CCY, CG_PER_PAGE, CG_PAGES, CG_CACHE_MIN,
    RSI_MIN_FAST, ADX_MIN_FAST, VOL_MULTIPLIER, NEEDED_OK_FAST,
    ADX_MIN_SLOW, EMA_TREND_SLOW, MACD_TREND_SLOW,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SLEEP_SECONDS, CONCURRENCY,
    MEXC_TICKER_24H_URL, MEXC_EXINFO_URL, MEXC_KLINES_URL,
    USE_FUTURES, FUTURES_KLINES_URL
)

print_lock = threading.Lock()
def log(*a):
    with print_lock:
        print(*a, flush=True)

# ----- HTTP sessions (cache cho CoinGecko) -----
session = requests.Session()
cg_session = CachedSession(
    cache_name="cg_cache",
    backend="memory",
    expire_after=timedelta(minutes=CG_CACHE_MIN),
)

def send_telegram(text: str):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        log("[WARN] Telegram env not set; msg skipped\n", text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        session.post(url, json=payload, timeout=15)
    except Exception as e:
        log("[ERR] telegram:", e)

# ---------- MEXC helpers ----------
def all_usdt_symbols() -> list[str]:
    r = session.get(MEXC_EXINFO_URL, timeout=20)
    r.raise_for_status()
    syms = []
    for s in r.json().get("symbols", []):
        sym = s.get("symbol","")
        if not sym.endswith("USDT"):
            continue
        if any(tag and tag in sym for tag in EXCLUDE_CONTAINS):
            continue
        syms.append(sym)
    return sorted(set(syms))

def ticker_24h_map() -> dict:
    r = session.get(MEXC_TICKER_24H_URL, timeout=25)
    r.raise_for_status()
    data = r.json()
    out = {}
    for t in data:
        sym = t.get("symbol")
        if not sym:
            continue
        try:
            t["quoteVolume"] = float(t.get("quoteVolume", 0.0))
            t["lastPrice"]   = float(t.get("lastPrice", 0.0))
        except:
            t["quoteVolume"] = 0.0
            t["lastPrice"]   = 0.0
        out[sym] = t
    return out

def klines_spot(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = session.get(MEXC_KLINES_URL, params=params, timeout=20)
    r.raise_for_status()
    raw = r.json()
    cols = ["open_time","open","high","low","close","volume","close_time",
            "quote_asset_volume","num_trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(raw, columns=cols)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"]  = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df

def klines_futures(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    i2s = {"1m":60, "5m":300, "15m":900, "30m":1800, "1h":3600, "4h":14400, "1d":86400}
    sec = i2s.get(interval, 3600)
    params = {"symbol": symbol.replace("USDT","_USDT"), "period": sec, "count": limit}
    r = session.get(FUTURES_KLINES_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        raise ValueError("Empty futures kline data")
    df = pd.DataFrame(data)
    df.rename(columns={"t":"open_time","o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = df["open_time"]
    return df

def fetch_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    return klines_futures(symbol, interval, limit) if USE_FUTURES else klines_spot(symbol, interval, limit)

# ---------- Indicators ----------
def with_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
    df["MACD"]   = macd["MACD_12_26_9"]
    df["SIGNAL"] = macd["MACDs_12_26_9"]
    df["RSI"]    = ta.rsi(df["close"], length=14)
    adx = ta.adx(df["high"], df["low"], df["close"], length=14)
    df["ADX"]    = adx["ADX_14"]
    df["VOL_SMA20"] = ta.sma(df["volume"], length=20)
    df["EMA200"] = ta.ema(df["close"], length=200)
    return df.dropna()

def cross_up(a: pd.Series, b: pd.Series) -> bool:
    if len(a) < 2 or len(b) < 2:
        return False
    return (a.iloc[-2] <= b.iloc[-2]) and (a.iloc[-1] > b.iloc[-1])

def fast_signal(df_fast: pd.DataFrame):
    last = df_fast.iloc[-1]
    checks = {
        "macd_cross_up": cross_up(df_fast["MACD"], df_fast["SIGNAL"]),
        "rsi_above":     bool(last["RSI"] >= RSI_MIN_FAST),
        "adx_trend":     bool(last["ADX"] >= ADX_MIN_FAST),
        "vol_surge":     bool(last["volume"] > VOL_MULTIPLIER * last.get("VOL_SMA20", math.inf)),
    }
    score = sum(1 for v in checks.values() if v)
    return (score >= NEEDED_OK_FAST, checks, score, last)

def slow_trend_ok(df_slow: pd.DataFrame):
    last = df_slow.iloc[-1]
    ok_adx  = (last["ADX"] >= ADX_MIN_SLOW)
    ok_ema  = (last["close"] >= last["EMA200"]) if EMA_TREND_SLOW else True
    ok_macd = (df_slow["MACD"].iloc[-1] > df_slow["SIGNAL"].iloc[-1]) if MACD_TREND_SLOW else True
    checks = {"adx_slow": ok_adx, "ema200_slow": ok_ema, "macd_slow": ok_macd}
    return (all(checks.values()), checks)

# ---------- CoinGecko enrich ----------
def cg_marketcaps_by_symbol() -> dict:
    out = {}
    for page in range(1, CG_PAGES + 1):
        params = {
            "vs_currency": CG_VS_CCY,
            "order": "market_cap_asc",
            "per_page": CG_PER_PAGE,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }
        try:
            r = cg_session.get("https://api.coingecko.com/api/v3/coins/markets", params=params, timeout=25)
            r.raise_for_status()
            arr = r.json()
            if not arr:
                break
            for it in arr:
                sym = (it.get("symbol") or "").upper()
                mc  = it.get("market_cap")
                if not sym or mc is None:
                    continue
                prev = out.get(sym)
                out[sym] = min(prev, mc) if prev is not None else mc
        except Exception as e:
            log("[CG] warn:", e)
            break
    return out

CG_CACHE = {"map": None, "last": 0.0}
def cg_get_map():
    now = time.time()
    if CG_CACHE["map"] is None or now - CG_CACHE["last"] > CG_CACHE_MIN * 60:
        CG_CACHE["map"] = cg_marketcaps_by_symbol()
        CG_CACHE["last"] = now
    return CG_CACHE["map"]

def marketcap_filter(symbol: str, tmap_24h: dict) -> bool:
    base = symbol[:-4].upper() if symbol.endswith("USDT") else symbol.upper()
    if USE_COINGECKO:
        cgmap = cg_get_map()
        mc = cgmap.get(base)
        if mc is not None:
            return mc > 0 and mc <= CG_MAX_MCAP_USD
    t = tmap_24h.get(symbol, {})
    qv = t.get("quoteVolume", 0.0)
    price = t.get("lastPrice", 0.0)
    if qv <= 0 or price < MIN_PRICE:
        return False
    return qv <= MAX_24H_QUOTE_VOL

# ---------- Pipeline ----------
def fmt_msg(sym: str, score: int, fast_checks: dict, slow_checks: dict, last_close: float, quoteVol: float, mcap_txt: str):
    fc = "\n".join([f"{'✅' if v else '❌'} {k}" for k,v in fast_checks.items()])
    sc = "\n".join([f"{'✅' if v else '❌'} {k}" for k,v in slow_checks.items()])
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"🚨 <b>{sym}</b> | Fast <b>{INTERVAL_FAST}</b> ↔ Slow <b>{INTERVAL_SLOW}</b>\n"
        f"Close: <b>{last_close:.8f}</b> | 24h qVol: <b>{quoteVol:,.0f}</b> USDT | {mcap_txt}\n"
        f"Score(Fast): <b>{score}</b>/4\n"
        f"{fc}\n"
        f"—— Slow confirm ——\n{sc}\n"
        f"{now}"
    )

def process_symbol(sym: str, tmap: dict, cgmap: dict | None):
    t = tmap.get(sym)
    if not t: return None
    if t.get("lastPrice", 0.0) < MIN_PRICE: return None

    keep = marketcap_filter(sym, tmap)
    if not keep: return None

    try:
        df_fast = fetch_klines(sym, INTERVAL_FAST, LIMIT)
        df_slow = fetch_klines(sym, INTERVAL_SLOW, LIMIT)
        if len(df_fast) < 80 or len(df_slow) < 80:
            return None

        df_fast = with_indicators(df_fast)
        df_slow = with_indicators(df_slow)
        if len(df_fast) < 30 or len(df_slow) < 30:
            return None

        is_sig, fast_checks, score, last_fast = fast_signal(df_fast)
        if not is_sig:
            return None
        ok_slow, slow_checks = slow_trend_ok(df_slow)
        if not ok_slow:
            return None

        mcap_txt = ""
        if USE_COINGECKO and cgmap is not None:
            base = sym[:-4].upper()
            mc = cgmap.get(base)
            if mc:
                mcap_txt = f"MC≈${mc:,.0f}"
            else:
                mcap_txt = "MC: n/a"
        else:
            mcap_txt = "MC: n/a"

        msg = fmt_msg(sym, score, fast_checks, slow_checks, float(last_fast["close"]), t.get("quoteVolume", 0.0), mcap_txt)
        return msg

    except Exception as e:
        log(f"[ERR] {sym} -> {e}")
        return None

def run_scan_once():
    syms = all_usdt_symbols()
    tmap = ticker_24h_map()
    cgmap = cg_get_map() if USE_COINGECKO else None

    candidates = [s for s in syms if s in tmap and tmap[s].get("lastPrice", 0.0) >= MIN_PRICE]
    log(f"[INFO] symbols={len(syms)} | candidates={len(candidates)} | CG={'on' if USE_COINGECKO else 'off'}")

    msgs = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futures = {ex.submit(process_symbol, s, tmap, cgmap): s for s in candidates}
        for fut in as_completed(futures):
            m = fut.result()
            if m:
                msgs.append(m)

    if not msgs:
        log("[INFO] No signals this round.")
        return

    block = "📈 <b>Tín hiệu micro-cap (CG + multi-TF)</b>\n" + "\n\n".join(msgs)
    log(block)
    send_telegram(block)

def main():
    log(f"Starting MEXC micro-cap scanner | FAST={INTERVAL_FAST} | SLOW={INTERVAL_SLOW} | CG<{CG_MAX_MCAP_USD:,.0f} USD | FUTURES={USE_FUTURES}")
    while True:
        try:
            run_scan_once()
        except Exception as e:
            log("[FATAL round]", e)
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()

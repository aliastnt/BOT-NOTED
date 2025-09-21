import os

def _b(name, default=False):
    return str(os.getenv(name, str(default))).strip().lower() in ("1","true","yes","on")

def _f(name, default):
    try: return float(os.getenv(name, str(default)))
    except: return default

def _i(name, default):
    try: return int(os.getenv(name, str(default)))
    except: return default

# ---------- Timeframe & dữ liệu ----------
INTERVAL_FAST = os.getenv("INTERVAL_FAST", "1h")  # TF tín hiệu (ví dụ 15m/1h)
INTERVAL_SLOW = os.getenv("INTERVAL_SLOW", "4h")  # TF xác nhận xu hướng
LIMIT         = _i("LIMIT", 300)

# ---------- “Micro-cap proxy” ban đầu (fallback nếu không dùng CG) ----------
MAX_24H_QUOTE_VOL = _f("MAX_24H_QUOTE_VOL", 5_000_000.0)
MIN_PRICE         = _f("MIN_PRICE", 0.0000001)
EXCLUDE_CONTAINS  = os.getenv("EXCLUDE_CONTAINS", "UP,DOWN,3L,3S,5L,5S").split(",")

# ---------- CoinGecko enrich ----------
USE_COINGECKO     = _b("USE_COINGECKO", True)
CG_MAX_MCAP_USD   = _f("CG_MAX_MCAP_USD", 50_000_000.0)  # < $50M
CG_VS_CCY         = os.getenv("CG_VS_CCY", "usd")
CG_PER_PAGE       = _i("CG_PER_PAGE", 250)               # mỗi trang
CG_PAGES          = _i("CG_PAGES", 4)                    # tối đa n trang (giới hạn rate)
CG_CACHE_MIN      = _i("CG_CACHE_MIN", 10)               # cache kết quả CG (phút)

# ---------- Chỉ báo & điều kiện ----------
RSI_MIN_FAST      = _f("RSI_MIN_FAST", 50.0)
ADX_MIN_FAST      = _f("ADX_MIN_FAST", 20.0)
VOL_MULTIPLIER    = _f("VOL_MULTIPLIER", 2.0)
NEEDED_OK_FAST    = _i("NEEDED_OK_FAST", 3)   # số điều kiện trong: macd_cross_up, rsi, adx, vol

# Lọc xu hướng trên TF chậm
ADX_MIN_SLOW      = _f("ADX_MIN_SLOW", 18.0)
EMA_TREND_SLOW    = _b("EMA_TREND_SLOW", True)   # giá > EMA200 trên 4h
MACD_TREND_SLOW   = _b("MACD_TREND_SLOW", True)  # MACD > Signal trên 4h

# ---------- Telegram ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------- Quét/Lặp ----------
SLEEP_SECONDS  = _i("SLEEP_SECONDS", 60)
CONCURRENCY    = _i("CONCURRENCY", 6)

# ---------- Nguồn dữ liệu ----------
MEXC_TICKER_24H_URL = "https://api.mexc.com/api/v3/ticker/24hr"
MEXC_EXINFO_URL     = "https://api.mexc.com/api/v3/exchangeInfo"
MEXC_KLINES_URL     = "https://api.mexc.com/api/v3/klines"
USE_FUTURES         = _b("USE_FUTURES", False)
FUTURES_KLINES_URL  = "https://contract.mexc.com/api/v1/contract/kline"

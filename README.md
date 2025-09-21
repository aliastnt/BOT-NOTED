# MEXC Micro-cap Scanner (CoinGecko + Multi-Timeframe)

Scanner quét **toàn bộ cặp USDT trên MEXC**, ưu tiên token **vốn hóa nhỏ** (dựa vào CoinGecko `< $50M`, fallback theo 24h quoteVolume) và lọc tín hiệu:
- **MACD cross up**
- **RSI > ngưỡng**
- **ADX > ngưỡng**
- **Volume surge** (Vol > MULT × SMA20)

Đồng thời yêu cầu **đồng thuận khung chậm (4h)**: ADX, EMA200, MACD.

## Cài đặt
```bash
pip install -r requirements.txt
cp .env.example .env   # điền TELEGRAM_* nếu muốn bắn cảnh báo
python scanner.py
```

## ENV chính
- `INTERVAL_FAST` / `INTERVAL_SLOW` : mặc định `1h` / `4h`
- `USE_COINGECKO=true` + `CG_MAX_MCAP_USD=50000000`
- Fallback proxy: `MAX_24H_QUOTE_VOL=5000000`
- Chỉ báo nhanh: `RSI_MIN_FAST=50`, `ADX_MIN_FAST=20`, `VOL_MULTIPLIER=2.0`, `NEEDED_OK_FAST=3`
- Xác nhận chậm: `ADX_MIN_SLOW=18`, `EMA_TREND_SLOW=true`, `MACD_TREND_SLOW=true`

## Gửi Telegram
Khai báo `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` để nhận cảnh báo.

## Dùng futures klines (tùy chọn)
Đặt `USE_FUTURES=true`. Lưu ý endpoint dùng format `BTC_USDT` và interval được map sang giây trong mã.

## Ghi chú
- Mapping CoinGecko theo **symbol** có thể trùng tên. Mã lấy **market cap nhỏ nhất** quan sát được cho ký hiệu đó (an toàn hơn). Có thể nâng cấp mapping theo **contract** nếu cần chính xác hơn.
- Hạn chế rate: đã dùng `requests-cache` cho CoinGecko (cache vài phút).
- Nên giữ `CONCURRENCY` 4–8 để an toàn.

# MarketDawn — setup guide

## 1. Subscribe to Kite Connect (₹500/month) — create an app

1. Go to **https://kite.trade** and log in with your Zerodha (Kite) account.
2. Click **Create new app** (you must create an app to get an API key).
3. **App type: choose `Connect`** — the ₹500/month plan that includes historical candles +
   realtime streaming. The free `Personal` plan does **not** include historical data, which
   MarketDawn needs.
4. Fill in:
   - **App name:** `MarketDawn` (any name)
   - **Redirect URL:** `https://127.0.0.1/` (placeholder is fine — we never place orders)
   - **Postback URL:** leave blank
   - **Description:** personal market analysis
5. **Create**, then confirm the **₹500/month** subscription.
6. Open the created app — you now have your **API key** and **API secret**.

> **About the SEBI static-IP notice on kite.trade:** it applies only to API **orders** from
> 1 Apr 2026. MarketDawn only *reads* data and never places orders, so this does **not**
> apply to us — you can ignore the static-IP step.

## 2. Collect the five secrets

| Secret | Where to find it |
| --- | --- |
| `KITE_API_KEY` | On the app page at kite.trade |
| `KITE_API_SECRET` | On the app page at kite.trade (click to reveal) |
| `KITE_USER_ID` | Your Zerodha client ID, e.g. `AB1234` |
| `KITE_PASSWORD` | Your Kite login password |
| `KITE_TOTP_SECRET` | The **TOTP secret** (base32 string) from your 2FA setup — *not* the 6-digit code. If you set up 2FA with an authenticator app, this is the key shown when you enabled it. If you only have the QR/app, you can re-enable external 2FA in Kite → Settings to reveal the secret. |

## 3. Store the secrets ENCRYPTED (no plaintext file)

Secrets are **not** kept in `.env`. Instead, run the secure setup command — it prompts for
each value with hidden input and saves it **encrypted in Windows Credential Manager**
(per-user, OS-encrypted). Nothing is written to disk in plaintext or committed to git.

```
.venv\Scripts\activate
python -m core.security.setup_credentials
```

- It asks for each secret one at a time (typing is hidden). Press Enter to skip an optional one.
- Check what's stored at any time (values are masked, never shown in full):

```
python -m core.security.setup_credentials --status
```

> Tell me once the required Kite secrets show ✓ and I'll run the data-accuracy gate to
> confirm every source is correct before building any signals on it.

## 4. (Optional) Telegram alerts

- In Telegram, message **@BotFather** → `/newbot` → follow prompts → copy the **bot token**
  into `TELEGRAM_BOT_TOKEN`.
- Message your new bot once, then get your **chat id** (I'll help) into `TELEGRAM_CHAT_ID`.

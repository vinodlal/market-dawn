from core.alerts.telegram import format_brief_message, MAX_LEN
from core.brief.morning_brief import assemble_brief


def _sample_brief():
    snapshot = {
        "NIFTY": {"last_price": 23800.55, "change_pct": 0.34},
        "GIFTNIFTY": {"last_price": None, "change_pct": None},
        "BANKNIFTY": {"last_price": 56592.0, "change_pct": -0.94},
    }
    news = {
        "india": [{"title": "Markets rally on strong earnings", "sentiment": "bullish"}],
        "global": [{"title": "Oil prices surge as war tensions rise", "sentiment": "bearish"}],
    }
    signals = [{
        "symbol": "BANKNIFTY", "bias": "Long", "score": 66, "confidence": "high",
        "reasons": ["Price near support: bullish (78/100)", "RSI momentum: bullish (64/100)"],
    }]
    return assemble_brief(snapshot, pcr=0.97, news_digest=news, top_signals=signals)


def test_format_brief_message_contains_key_sections():
    msg = format_brief_message(_sample_brief())
    assert "<b>MarketDawn — Pre-open Brief</b>" in msg
    assert "<b>Snapshot</b>" in msg
    assert "NIFTY  23,800.55  ▲ +0.34%" in msg
    assert "GIFTNIFTY: unavailable" in msg
    assert "PCR (Bank Nifty): 0.97" in msg
    assert "<b>Top signals</b>" in msg
    assert "<b>BANKNIFTY</b> ▲ LONG (score 66, high confidence)" in msg
    assert "Price near support: bullish (78/100)" in msg
    assert "Markets rally on strong earnings" in msg
    assert "Oil prices surge as war tensions rise" in msg
    assert "Not SEBI-registered investment advice" in msg


def test_format_brief_message_html_escapes_dynamic_content():
    snapshot = {"NIFTY": {"last_price": 100.0, "change_pct": 0.0}}
    news = {"india": [{"title": "Tata & Sons < 5% stake move", "sentiment": "neutral"}], "global": []}
    brief = assemble_brief(snapshot, pcr=None, news_digest=news, top_signals=[])
    msg = format_brief_message(brief)
    assert "Tata &amp; Sons &lt; 5% stake move" in msg
    assert "Tata & Sons < 5%" not in msg  # raw unescaped form must not appear


def test_format_brief_message_within_telegram_length_limit():
    msg = format_brief_message(_sample_brief())
    assert len(msg) <= MAX_LEN


def test_format_brief_message_handles_no_signals_or_news():
    brief = assemble_brief({}, pcr=None, news_digest={"india": [], "global": []}, top_signals=[])
    msg = format_brief_message(brief)
    assert "<b>MarketDawn" in msg
    assert "Top signals" not in msg

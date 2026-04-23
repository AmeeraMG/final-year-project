"""
nlp_module.py
─────────────
Converts structured ML prediction results into human-readable
business insights in English and Tamil.
"""


def generate_insights(ml_results: dict) -> dict:
    """
    Takes the output dict from RetailMLSystem.run() and returns
    a dict with 'english' and 'tamil' message strings.
    """
    summary      = ml_results.get("summary", {})
    forecast     = ml_results.get("forecast", {})
    trends       = ml_results.get("trends", [])
    stock_alerts = ml_results.get("stock_alerts", {})
    insights     = ml_results.get("insights", [])

    english = _build_english(summary, forecast, trends, stock_alerts, insights)
    tamil   = _build_tamil(summary, forecast, trends, stock_alerts, insights)

    return {"english": english, "tamil": tamil}


# ─── English message builder ──────────────────────────────────────────────────

def _build_english(summary, forecast, trends, stock_alerts, insights):
    lines = []
    lines.append("Hello,")
    lines.append("")
    lines.append("Your sales data has been analyzed. Here is your business intelligence report:")
    lines.append("")

    # Sales forecast
    pred  = forecast.get("predicted_sales", 0)
    chg   = forecast.get("change_pct", 0)
    fdate = forecast.get("forecast_date", "tomorrow")
    direction = "increase" if chg >= 0 else "decrease"
    lines.append(f"📊 Sales Forecast:")
    lines.append(f"   Tomorrow ({fdate}) predicted sales: ₹{pred:,.0f}")
    lines.append(f"   Expected to {direction} by {abs(chg):.1f}% compared to today.")
    lines.append("")

    # Trend analysis
    lines.append("📈 Trend Analysis:")
    if trends:
        for t in trends[:3]:
            product   = t["product"]
            direction_label = t["direction"].split(" ", 1)[1]  # remove emoji
            lines.append(f"   • {product}: {direction_label}")
    else:
        lines.append("   No trend data available.")
    lines.append("")

    # Stock recommendations
    lines.append("📦 Stock Recommendation:")
    critical = stock_alerts.get("critical", [])
    low      = stock_alerts.get("low", [])
    if critical:
        for item in critical[:3]:
            lines.append(f"   🔴 {item['product'].title()} — CRITICAL: only {item['days_left']} days of stock left. Order {item['order_qty']} units immediately.")
    if low:
        for item in low[:3]:
            lines.append(f"   🟡 {item['product'].title()} — LOW: {item['days_left']} days left. Order {item['order_qty']} units soon.")
    if not critical and not low:
        lines.append("   ✅ All stock levels are healthy. No urgent orders needed.")
    lines.append("")

    # Business insights
    lines.append("💡 Business Insights:")
    for insight in insights:
        lines.append(f"   {insight['icon']} {insight['message']}")
    lines.append("")

    lines.append("Thank you for using Sales Intelligence.")
    lines.append("Please review the full report on the portal for detailed charts and data.")

    return "\n".join(lines)


# ─── Tamil message builder ────────────────────────────────────────────────────

def _build_tamil(summary, forecast, trends, stock_alerts, insights):
    lines = []
    lines.append("வணக்கம்,")
    lines.append("")
    lines.append("உங்கள் விற்பனை தரவு பகுப்பாய்வு செய்யப்பட்டுள்ளது. இதோ உங்கள் வணிக அறிக்கை:")
    lines.append("")

    # Sales forecast in Tamil
    pred  = forecast.get("predicted_sales", 0)
    chg   = forecast.get("change_pct", 0)
    fdate = forecast.get("forecast_date", "நாளை")
    direction_ta = "அதிகரிக்கும்" if chg >= 0 else "குறையும்"
    lines.append("📊 விற்பனை கணிப்பு:")
    lines.append(f"   நாளை ({fdate}) எதிர்பார்க்கப்படும் விற்பனை: ₹{pred:,.0f}")
    lines.append(f"   இன்றை விற்பனையை விட {abs(chg):.1f}% {direction_ta}.")
    lines.append("")

    # Trend analysis in Tamil
    lines.append("📈 போக்கு பகுப்பாய்வு:")
    trend_map = {
        "Rising" : "அதிகரிக்கிறது",
        "Falling": "குறைகிறது",
        "Stable" : "நிலையாக உள்ளது",
    }
    if trends:
        for t in trends[:3]:
            product   = t["product"]
            d_raw     = t["direction"]
            # extract english keyword
            ta_dir = "நிலையாக உள்ளது"
            for key, val in trend_map.items():
                if key in d_raw:
                    ta_dir = val
                    break
            lines.append(f"   • {product}: {ta_dir}")
    else:
        lines.append("   போக்கு தரவு கிடைக்கவில்லை.")
    lines.append("")

    # Stock in Tamil
    lines.append("📦 பங்கு பரிந்துரை:")
    critical = stock_alerts.get("critical", [])
    low      = stock_alerts.get("low", [])
    if critical:
        for item in critical[:3]:
            lines.append(f"   🔴 {item['product'].title()} — மிக குறைவு: {item['days_left']} நாட்கள் மட்டுமே உள்ளது. உடனே {item['order_qty']} தொகுதிகள் ஆர்டர் செய்யுங்கள்.")
    if low:
        for item in low[:3]:
            lines.append(f"   🟡 {item['product'].title()} — குறைவு: {item['days_left']} நாட்கள் மட்டுமே உள்ளது. {item['order_qty']} தொகுதிகள் ஆர்டர் செய்யுங்கள்.")
    if not critical and not low:
        lines.append("   ✅ அனைத்து பங்குகளும் நல்ல நிலையில் உள்ளன. அவசர ஆர்டர் தேவையில்லை.")
    lines.append("")

    # Insights in Tamil
    lines.append("💡 வணிக அறிவுரை:")
    insight_translations = {
        "sales_performance": lambda m: f"   📊 {_translate_sales_perf(m)}",
        "stock_alert"      : lambda m: f"   🚨 சில பொருட்கள் மிக குறைவாக உள்ளன — உடனே ஆர்டர் செய்யவும்.",
        "rising_demand"    : lambda m: f"   🔥 தேவை அதிகரிக்கும் பொருட்கள் உள்ளன — மறு-ஆர்டர் அளவை அதிகரிக்கவும்.",
        "declining"        : lambda m: f"   ⚠️ சில பொருட்களின் விற்பனை குறைகிறது — அதிகமாக ஆர்டர் செய்வதை தவிர்க்கவும்.",
        "all_clear"        : lambda m: f"   ✅ அனைத்தும் நல்ல நிலையில் உள்ளன — அவசர நடவடிக்கை தேவையில்லை.",
    }
    for insight in insights:
        itype = insight.get("type", "")
        imsg  = insight.get("message", "")
        if itype in insight_translations:
            lines.append(insight_translations[itype](imsg))
        else:
            lines.append(f"   {insight.get('icon', '')} {imsg}")
    lines.append("")

    lines.append("Sales Intelligence சேவையை பயன்படுத்தியதற்கு நன்றி.")
    lines.append("முழு அறிக்கையை போர்டலில் பார்க்கவும்.")

    return "\n".join(lines)


def _translate_sales_perf(message: str) -> str:
    """Simple pattern-based translation for sales performance message"""
    if "above" in message or "strong" in message:
        return "இன்றைய விற்பனை தினசரி சராசரியை விட அதிகமாக உள்ளது — சிறப்பான வணிக நாள்."
    else:
        return "இன்றைய விற்பனை தினசரி சராசரியை விட குறைவாக உள்ளது — மந்தமான வணிக நாள்."

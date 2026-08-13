import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FRANKFURTER_BASE = "https://api.frankfurter.dev/v1"
CURRENCY_API_BASE = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api"

TREND_THRESHOLD_PCT = 0.15
VOLATILITY_THRESHOLDS_PCT = (0.25, 0.6)
FALLBACK_MAX_DAYS = 90
FALLBACK_MAX_WORKERS = 20

# Frankfurter (ECB reference rates) only covers ~30 major currencies. For
# everything else we fall back to a broader, free, no-key community dataset
# (see fetch_history_fallback) so effectively every ISO 4217 currency in
# active use is searchable, not just majors.
FRANKFURTER_CURRENCIES = {
    "AUD", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP", "HKD",
    "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN", "MYR", "NOK",
    "NZD", "PHP", "PLN", "RON", "SEK", "SGD", "THB", "TRY", "USD", "ZAR",
}

CURRENCY_NAMES = {
    "AED": "UAE Dirham", "AFN": "Afghan Afghani", "ALL": "Albanian Lek",
    "AMD": "Armenian Dram", "ANG": "Netherlands Antillean Guilder",
    "AOA": "Angolan Kwanza", "ARS": "Argentine Peso", "AUD": "Australian Dollar",
    "AWG": "Aruban Florin", "AZN": "Azerbaijani Manat",
    "BAM": "Bosnia-Herzegovina Convertible Mark", "BBD": "Barbadian Dollar",
    "BDT": "Bangladeshi Taka", "BGN": "Bulgarian Lev", "BHD": "Bahraini Dinar",
    "BIF": "Burundian Franc", "BMD": "Bermudian Dollar", "BND": "Brunei Dollar",
    "BOB": "Bolivian Boliviano", "BRL": "Brazilian Real", "BSD": "Bahamian Dollar",
    "BTN": "Bhutanese Ngultrum", "BWP": "Botswana Pula", "BYN": "Belarusian Ruble",
    "BZD": "Belize Dollar", "CAD": "Canadian Dollar", "CDF": "Congolese Franc",
    "CHF": "Swiss Franc", "CLP": "Chilean Peso", "CNY": "Chinese Yuan",
    "COP": "Colombian Peso", "CRC": "Costa Rican Colon", "CUP": "Cuban Peso",
    "CVE": "Cape Verdean Escudo", "CZK": "Czech Koruna", "DJF": "Djiboutian Franc",
    "DKK": "Danish Krone", "DOP": "Dominican Peso", "DZD": "Algerian Dinar",
    "EGP": "Egyptian Pound", "ERN": "Eritrean Nakfa", "ETB": "Ethiopian Birr",
    "EUR": "Euro", "FJD": "Fijian Dollar", "FKP": "Falkland Islands Pound",
    "GBP": "British Pound", "GEL": "Georgian Lari", "GHS": "Ghanaian Cedi",
    "GIP": "Gibraltar Pound", "GMD": "Gambian Dalasi", "GNF": "Guinean Franc",
    "GTQ": "Guatemalan Quetzal", "GYD": "Guyanaese Dollar", "HKD": "Hong Kong Dollar",
    "HNL": "Honduran Lempira", "HTG": "Haitian Gourde", "HUF": "Hungarian Forint",
    "IDR": "Indonesian Rupiah", "ILS": "Israeli New Shekel", "INR": "Indian Rupee",
    "IQD": "Iraqi Dinar", "IRR": "Iranian Rial", "ISK": "Icelandic Krona",
    "JMD": "Jamaican Dollar", "JOD": "Jordanian Dinar", "JPY": "Japanese Yen",
    "KES": "Kenyan Shilling", "KGS": "Kyrgystani Som", "KHR": "Cambodian Riel",
    "KMF": "Comorian Franc", "KRW": "South Korean Won", "KWD": "Kuwaiti Dinar",
    "KYD": "Cayman Islands Dollar", "KZT": "Kazakhstani Tenge", "LAK": "Laotian Kip",
    "LBP": "Lebanese Pound", "LKR": "Sri Lankan Rupee", "LRD": "Liberian Dollar",
    "LSL": "Lesotho Loti", "LYD": "Libyan Dinar", "MAD": "Moroccan Dirham",
    "MDL": "Moldovan Leu", "MGA": "Malagasy Ariary", "MKD": "Macedonian Denar",
    "MMK": "Myanma Kyat", "MNT": "Mongolian Tugrik", "MOP": "Macanese Pataca",
    "MRU": "Mauritanian Ouguiya", "MUR": "Mauritian Rupee", "MVR": "Maldivian Rufiyaa",
    "MWK": "Malawian Kwacha", "MXN": "Mexican Peso", "MYR": "Malaysian Ringgit",
    "MZN": "Mozambican Metical", "NAD": "Namibian Dollar", "NGN": "Nigerian Naira",
    "NIO": "Nicaraguan Cordoba", "NOK": "Norwegian Krone", "NPR": "Nepalese Rupee",
    "NZD": "New Zealand Dollar", "OMR": "Omani Rial", "PAB": "Panamanian Balboa",
    "PEN": "Peruvian Sol", "PGK": "Papua New Guinean Kina", "PHP": "Philippine Peso",
    "PKR": "Pakistani Rupee", "PLN": "Polish Zloty", "PYG": "Paraguayan Guarani",
    "QAR": "Qatari Rial", "RON": "Romanian Leu", "RSD": "Serbian Dinar",
    "RUB": "Russian Ruble", "RWF": "Rwandan Franc", "SAR": "Saudi Riyal",
    "SBD": "Solomon Islands Dollar", "SCR": "Seychellois Rupee", "SDG": "Sudanese Pound",
    "SEK": "Swedish Krona", "SGD": "Singapore Dollar", "SHP": "Saint Helena Pound",
    "SLE": "Sierra Leonean Leone", "SOS": "Somali Shilling", "SRD": "Surinamese Dollar",
    "SSP": "South Sudanese Pound", "STN": "Sao Tome and Principe Dobra",
    "SZL": "Swazi Lilangeni", "THB": "Thai Baht", "TJS": "Tajikistani Somoni",
    "TMT": "Turkmenistani Manat", "TND": "Tunisian Dinar", "TOP": "Tongan Paanga",
    "TRY": "Turkish Lira", "TTD": "Trinidad and Tobago Dollar", "TWD": "New Taiwan Dollar",
    "TZS": "Tanzanian Shilling", "UAH": "Ukrainian Hryvnia", "UGX": "Ugandan Shilling",
    "USD": "US Dollar", "UYU": "Uruguayan Peso", "UZS": "Uzbekistani Som",
    "VES": "Venezuelan Bolivar", "VND": "Vietnamese Dong", "VUV": "Vanuatu Vatu",
    "WST": "Samoan Tala", "XAF": "Central African CFA Franc",
    "XCD": "East Caribbean Dollar", "XOF": "West African CFA Franc",
    "XPF": "CFP Franc", "YER": "Yemeni Rial", "ZAR": "South African Rand",
    "ZMW": "Zambian Kwacha", "ZWL": "Zimbabwean Dollar",
}


def fetch_history_frankfurter(base: str, target: str, days: int):
    end = date.today()
    start = end - timedelta(days=days)
    resp = requests.get(
        f"{FRANKFURTER_BASE}/{start.isoformat()}..{end.isoformat()}",
        params={"from": base, "to": target},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    series = sorted(data["rates"].items())
    return [{"date": d, "rate": rates[target]} for d, rates in series]


def _fetch_fallback_day(base_lower: str, target_lower: str, day: date):
    url = f"{CURRENCY_API_BASE}@{day.isoformat()}/v1/currencies/{base_lower}.json"
    try:
        resp = requests.get(url, timeout=6)
        if resp.status_code != 200:
            return None
        rate = resp.json().get(base_lower, {}).get(target_lower)
    except requests.RequestException:
        return None
    return {"date": day.isoformat(), "rate": rate} if rate is not None else None


def fetch_history_fallback(base: str, target: str, days: int):
    """Broader-coverage historical source for currencies outside Frankfurter's ~30.

    This community dataset publishes one JSON snapshot per calendar day rather
    than a range endpoint, so history is assembled from parallel per-day
    fetches (capped at FALLBACK_MAX_DAYS to keep total latency reasonable).
    """
    days = min(days, FALLBACK_MAX_DAYS)
    end = date.today()
    start = end - timedelta(days=days)
    all_days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    base_lower, target_lower = base.lower(), target.lower()

    points = {}
    with ThreadPoolExecutor(max_workers=FALLBACK_MAX_WORKERS) as executor:
        futures = [executor.submit(_fetch_fallback_day, base_lower, target_lower, d) for d in all_days]
        for future in as_completed(futures):
            point = future.result()
            if point:
                points[point["date"]] = point

    return [points[d] for d in sorted(points)]


def fetch_history(base: str, target: str, days: int):
    if base in FRANKFURTER_CURRENCIES and target in FRANKFURTER_CURRENCIES:
        return fetch_history_frankfurter(base, target, days)
    return fetch_history_fallback(base, target, days)


def linear_regression_forecast(series, forecast_days: int):
    """Least-squares linear fit over the historical series, projected forward.

    This is a simple trend line, not a real financial forecasting model —
    exchange rates are close to a random walk and short trend lines are a
    weak predictor. It's presented as a straightforward, honestly-labeled
    demonstration of a regression-based prediction, not investment advice.
    """
    n = len(series)
    xs = list(range(n))
    ys = [point["rate"] for point in series]

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs) or 1e-9
    slope = num / den
    intercept = mean_y - slope * mean_x

    last_date = date.fromisoformat(series[-1]["date"])
    predictions = []
    for i in range(1, forecast_days + 1):
        x = n - 1 + i
        predicted_rate = slope * x + intercept
        predictions.append(
            {
                "date": (last_date + timedelta(days=i)).isoformat(),
                "rate": round(predicted_rate, 6),
            }
        )
    return predictions, slope


def classify_trend(pct_change: float) -> str:
    if pct_change > TREND_THRESHOLD_PCT:
        return "upward"
    if pct_change < -TREND_THRESHOLD_PCT:
        return "downward"
    return "flat"


def compute_volatility(history):
    """Daily-return volatility (population stdev, in percent) over the window.

    A rough, illustrative measure of how noisy this pair has been recently —
    not a rigorous risk model, just enough to caveat the trend appropriately.
    """
    returns = [
        (curr["rate"] - prev["rate"]) / prev["rate"] * 100
        for prev, curr in zip(history, history[1:])
        if prev["rate"]
    ]
    if not returns:
        return 0.0, "low"
    vol = statistics.pstdev(returns)
    low, high = VOLATILITY_THRESHOLDS_PCT
    label = "low" if vol < low else "moderate" if vol < high else "high"
    return round(vol, 3), label


def build_insights(base: str, target: str, trend: str, volatility_label: str):
    """Rule-based FX-trend commentary for three audiences.

    Deliberately generic and educational, not personalized advice: it maps
    trend direction + recent volatility to standard, textbook FX-exposure
    talking points (competitiveness, import costs, debt service, hedging,
    timing risk). Always paired with a disclaimer in the response.
    """
    if trend == "downward":
        government = {
            "stance": f"{base} has been weakening against {target}",
            "points": [
                f"Imports priced in {target} get more expensive in {base} terms — watch pass-through to domestic inflation, especially for essentials like fuel, food, and medical supplies.",
                f"A weaker {base} improves price competitiveness for {base}-priced exports — export-promotion tools (trade financing, credit guarantees) can help capitalize on the window.",
                f"Debt service on {target}-denominated obligations gets costlier in {base} terms — prioritize FX reserve buffers and consider hedging near-term external debt.",
                "Persistent depreciation raises the case for monetary tightening to defend the currency and contain imported inflation — weigh the growth trade-off, and lean on clear communication and reserve intervention before abrupt rate moves.",
            ],
        }
        trade = {
            "stance": f"Favorable window for {base}-based exporters",
            "points": [
                f"Exporters: goods priced in {base} are now cheaper for {target}-based buyers — consider locking in the improved competitiveness with longer contracts or forward FX sales.",
                f"Importers: input costs priced in {target} are rising — hedge remaining {target} purchases with forward contracts and review supplier contracts for price-adjustment clauses.",
                "The bigger the swing, the more a standing hedging policy (forwards/options) beats budgeting off the spot rate.",
            ],
        }
        individual = {
            "stance": f"Your {base} buys less {target} than it did",
            "points": [
                f"Need {target} soon for travel, tuition, or remittances? Converting sooner rather than waiting may beat further depreciation — but don't rush a large lump sum on one data point.",
                f"Receiving income or remittances in {target}? Each unit now converts to more {base} — a relatively good time to bring it home if that was the plan anyway.",
                "Spread large conversions over several weeks instead of one transaction to reduce the risk of unlucky timing.",
            ],
        }
    elif trend == "upward":
        government = {
            "stance": f"{base} has been strengthening against {target}",
            "points": [
                f"Cheaper {target}-priced imports ease imported-inflation pressure — a supportive backdrop for holding rates steady if inflation is already near target.",
                f"Exporters pricing in {base} become less competitive abroad — monitor export-sector output and employment, and support diversification into higher-value goods less sensitive to price alone.",
                "A strengthening currency can attract capital inflows — watch for asset-price or credit-growth overheating, and favor macroprudential tools over currency intervention as a first response.",
                f"External debt service on {target}-denominated obligations gets cheaper in {base} terms — a window to reduce debt stock at a lower relative cost.",
            ],
        }
        trade = {
            "stance": f"Favorable window for {base}-based importers",
            "points": [
                f"Importers: {target}-priced inputs are relatively cheap right now — consider forward-buying if storage and working capital allow.",
                f"Exporters: pricing is less competitive abroad — hedge future {target} receivables with forward sales to protect margins, or revisit pricing and product mix for price-sensitive markets.",
                "Consider whether a standing hedging program fits your risk tolerance better than one-off conversions timed to the market.",
            ],
        }
        individual = {
            "stance": f"Your {base} buys more {target} than it did",
            "points": [
                f"Upcoming travel, tuition, or purchases priced in {target}? This is a relatively favorable window to convert.",
                f"Receiving income in {target}? Converting to {base} now yields less than before — consider delaying non-urgent conversions.",
                "As always, spread large one-off conversions over time rather than converting everything at once.",
            ],
        }
    else:
        government = {
            "stance": f"{base}/{target} has been range-bound",
            "points": [
                "Stable FX conditions support medium-term fiscal and infrastructure planning that depends on import costs or FX-denominated financing.",
                "A calm period is a good window to rebuild FX reserve buffers opportunistically without moving the market.",
                "Keep watching underlying trade-balance and current-account trends — spot-rate stability can mask building imbalances.",
            ],
        }
        trade = {
            "stance": "Low-volatility window — good for planning, not for timing",
            "points": [
                "Stable rates lower the payoff from trying to time conversions — focus on operational efficiency and diversifying currency exposure instead.",
                "Good time to set up or review a standing hedging policy (e.g. laddered forward contracts) for predictable future receivables and payables.",
            ],
        }
        individual = {
            "stance": "Rates have been fairly stable",
            "points": [
                "No strong timing signal either way — prioritize convenience and low fees over trying to time the market.",
                "A stable stretch is a reasonable time to set a budget or savings plan in either currency without worrying about near-term swings.",
            ],
        }

    volatility_notes = {
        "high": "Daily moves on this pair have been more volatile than usual recently — treat the direction with extra caution and favor hedging over prediction.",
        "moderate": "Day-to-day swings have been moderate lately — normal FX noise, not a strong signal on its own.",
        "low": "Day-to-day moves have been unusually calm recently — a good window to plan without fighting short-term noise.",
    }
    for section in (government, trade, individual):
        section["points"].append(volatility_notes[volatility_label])

    return {
        "government": government,
        "trade": trade,
        "individual": individual,
        "disclaimer": (
            "General, rule-based observations drawn from this pair's recent trend and volatility — "
            "not personalized financial, investment, or policy advice. For decisions that matter, "
            "consult a licensed financial advisor or economist."
        ),
    }


@app.get("/api/currencies")
def currencies():
    return jsonify(CURRENCY_NAMES)


@app.get("/api/predict")
def predict():
    base = request.args.get("base", "USD").upper()
    target = request.args.get("target", "EUR").upper()
    days = min(int(request.args.get("days", 30)), 180)
    forecast_days = min(int(request.args.get("forecast", 7)), 30)

    if base == target:
        return jsonify({"error": "base and target currencies must differ"}), 400

    try:
        history = fetch_history(base, target, days)
    except requests.RequestException as exc:
        return jsonify({"error": f"upstream rate API failed: {exc}"}), 502

    if len(history) < 3:
        return jsonify({"error": "not enough historical data returned"}), 502

    predictions, slope = linear_regression_forecast(history, forecast_days)

    latest_rate = history[-1]["rate"]
    forecast_rate = predictions[-1]["rate"]
    pct_change_forecast = (forecast_rate - latest_rate) / latest_rate * 100
    trend = classify_trend(pct_change_forecast)
    volatility_pct, volatility_label = compute_volatility(history)

    return jsonify(
        {
            "base": base,
            "target": target,
            "history": history,
            "predictions": predictions,
            "trend": trend,
            "pct_change_forecast": round(pct_change_forecast, 3),
            "volatility": {"value": volatility_pct, "label": volatility_label},
            "insights": build_insights(base, target, trend, volatility_label),
            "disclaimer": "Simple linear-regression trend line over recent history — "
            "not a financial forecasting model or investment advice.",
        }
    )

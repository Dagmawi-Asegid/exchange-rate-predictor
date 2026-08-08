from datetime import date, timedelta

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FRANKFURTER_BASE = "https://api.frankfurter.app"


def fetch_history(base: str, target: str, days: int):
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


@app.get("/api/currencies")
def currencies():
    resp = requests.get(f"{FRANKFURTER_BASE}/currencies", timeout=10)
    resp.raise_for_status()
    return jsonify(resp.json())


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

    return jsonify(
        {
            "base": base,
            "target": target,
            "history": history,
            "predictions": predictions,
            "trend": "upward" if slope > 0 else "downward" if slope < 0 else "flat",
            "disclaimer": "Simple linear-regression trend line over recent history — "
            "not a financial forecasting model or investment advice.",
        }
    )


if __name__ == "__main__":
    app.run(port=5050, debug=True)

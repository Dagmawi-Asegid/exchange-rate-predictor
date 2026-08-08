# Exchange Rate Predictor

Full-stack app that pulls live currency exchange rate history from the free
[Frankfurter API](https://frankfurter.dev/) and projects a short-term trend
forward using a simple least-squares linear regression, plotted with Chart.js.

The forecast is deliberately simple and labeled as such in the UI — it's a
straight trend line over recent history, not a real financial forecasting
model, since exchange rates are close to a random walk.

## Stack

- **Frontend**: React (Vite), Chart.js / react-chartjs-2
- **Backend**: Flask REST API (`/api/currencies`, `/api/predict`), proxying and
  computing over live Frankfurter data

## Run locally

Backend:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 app.py            # http://localhost:5050
```

Frontend:

```bash
npm install
npm run dev                # http://localhost:5173
```

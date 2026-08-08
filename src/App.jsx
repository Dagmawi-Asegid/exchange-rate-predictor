import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import "./App.css";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const API_BASE = import.meta.env.DEV ? "http://localhost:5050" : "";

function App() {
  const [currencies, setCurrencies] = useState({});
  const [base, setBase] = useState("USD");
  const [target, setTarget] = useState("EUR");
  const [days, setDays] = useState(30);
  const [forecastDays, setForecastDays] = useState(7);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/currencies`)
      .then((res) => res.json())
      .then(setCurrencies)
      .catch(() => setError("Couldn't load currency list — is the Flask API running on :5050?"));
  }, []);

  useEffect(() => {
    if (base === target) return;
    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/predict?base=${base}&target=${target}&days=${days}&forecast=${forecastDays}`)
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Request failed");
        return data;
      })
      .then(setResult)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [base, target, days, forecastDays]);

  const chartData = result && {
    labels: [...result.history.map((p) => p.date), ...result.predictions.map((p) => p.date)],
    datasets: [
      {
        label: `${base}/${target} — historical`,
        data: result.history.map((p) => p.rate),
        borderColor: "#4f7cff",
        backgroundColor: "rgba(79,124,255,0.1)",
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.2,
      },
      {
        label: `${base}/${target} — predicted`,
        data: [
          ...Array(result.history.length - 1).fill(null),
          result.history[result.history.length - 1].rate,
          ...result.predictions.map((p) => p.rate),
        ],
        borderColor: "#ff9f43",
        borderDash: [6, 4],
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.2,
      },
    ],
  };

  const currencyOptions = Object.entries(currencies);

  return (
    <div className="app">
      <header>
        <h1>Exchange Rate Predictor</h1>
        <p className="subtitle">Live FX history with a simple linear-trend forecast</p>
      </header>

      <div className="controls">
        <label>
          From
          <select value={base} onChange={(e) => setBase(e.target.value)}>
            {currencyOptions.map(([code, name]) => (
              <option key={code} value={code}>{code} — {name}</option>
            ))}
          </select>
        </label>
        <label>
          To
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {currencyOptions.map(([code, name]) => (
              <option key={code} value={code}>{code} — {name}</option>
            ))}
          </select>
        </label>
        <label>
          History (days)
          <input type="number" min="7" max="180" value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <label>
          Forecast (days)
          <input type="number" min="1" max="30" value={forecastDays} onChange={(e) => setForecastDays(Number(e.target.value))} />
        </label>
      </div>

      {base === target && <p className="error">Pick two different currencies.</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p className="status">Loading…</p>}

      {result && !loading && (
        <>
          <div className="summary">
            <div>
              <span className="label">Latest rate</span>
              <span className="value">1 {base} = {result.history[result.history.length - 1].rate} {target}</span>
            </div>
            <div>
              <span className="label">Trend</span>
              <span className={`value trend ${result.trend}`}>{result.trend}</span>
            </div>
            <div>
              <span className="label">
                {forecastDays}-day forecast
              </span>
              <span className="value">
                1 {base} = {result.predictions[result.predictions.length - 1].rate} {target}
              </span>
            </div>
          </div>
          <div className="chart-wrap">
            <Line data={chartData} options={{ responsive: true, plugins: { legend: { labels: { color: "#c9d1e0" } } }, scales: { x: { ticks: { color: "#8b93a7", maxTicksLimit: 8 } }, y: { ticks: { color: "#8b93a7" } } } }} />
          </div>
          <p className="disclaimer">{result.disclaimer}</p>
        </>
      )}
    </div>
  );
}

export default App;

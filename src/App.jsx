import { useEffect, useMemo, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import MarketScene from "./MarketScene";
import "./App.css";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const API_BASE = import.meta.env.DEV ? "http://localhost:5050" : "";

const PRESET_PAIRS = [
  { base: "USD", target: "EUR" },
  { base: "USD", target: "JPY" },
  { base: "USD", target: "INR" },
  { base: "USD", target: "ZAR" },
  { base: "GBP", target: "USD" },
  { base: "EUR", target: "GBP" },
  { base: "USD", target: "MXN" },
  { base: "USD", target: "CNY" },
];

const TREND_META = {
  upward: { arrow: "▲", label: "Upward", className: "upward" },
  downward: { arrow: "▼", label: "Downward", className: "downward" },
  flat: { arrow: "→", label: "Flat", className: "flat" },
};

const INSIGHT_TABS = [
  { key: "government", icon: "🏛️", label: "Government & Policy" },
  { key: "trade", icon: "📦", label: "Exporters & Importers" },
  { key: "individual", icon: "👤", label: "Individuals" },
];

function App() {
  const [currencies, setCurrencies] = useState({});
  const [base, setBase] = useState("USD");
  const [target, setTarget] = useState("EUR");
  const [days, setDays] = useState(30);
  const [forecastDays, setForecastDays] = useState(7);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("government");

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

  const swapCurrencies = () => {
    setBase(target);
    setTarget(base);
  };

  const chartData = result && {
    labels: [...result.history.map((p) => p.date), ...result.predictions.map((p) => p.date)],
    datasets: [
      {
        label: `${base}/${target} — historical`,
        data: result.history.map((p) => p.rate),
        borderColor: "#4f7cff",
        backgroundColor: "rgba(79,124,255,0.12)",
        pointRadius: 0,
        borderWidth: 2,
        tension: 0.25,
        fill: true,
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
        tension: 0.25,
      },
    ],
  };

  const tickerText = useMemo(() => {
    if (!result) return "";
    const meta = TREND_META[result.trend];
    const latest = result.history[result.history.length - 1].rate;
    const forecastRate = result.predictions[result.predictions.length - 1].rate;
    const pct = result.pct_change_forecast;
    return `${result.base}/${result.target}  ${latest.toFixed(4)}  ${meta.arrow}  ${pct > 0 ? "+" : ""}${pct}% over ${forecastDays}d  →  forecast ${forecastRate.toFixed(4)}  ·  volatility: ${result.volatility.label}`;
  }, [result, forecastDays]);

  const currencyOptions = Object.entries(currencies);
  const trendMeta = result ? TREND_META[result.trend] : null;

  return (
    <>
      <MarketScene trend={result?.trend ?? "flat"} volatilityLabel={result?.volatility?.label ?? "low"} tickerText={tickerText} />
      <div className="app">
        <header>
          <h1>Exchange Rate Predictor</h1>
          <p className="subtitle">
            Live FX history, a simple trend forecast, and plain-language takeaways for policymakers,
            trade businesses, and individuals.
          </p>
        </header>

        <div className="preset-row">
          {PRESET_PAIRS.map((pair) => (
            <button
              key={`${pair.base}${pair.target}`}
              type="button"
              className={`preset-chip ${base === pair.base && target === pair.target ? "active" : ""}`}
              onClick={() => {
                setBase(pair.base);
                setTarget(pair.target);
              }}
            >
              {pair.base}/{pair.target}
            </button>
          ))}
        </div>

        <div className="controls">
          <label>
            From
            <select value={base} onChange={(e) => setBase(e.target.value)}>
              {currencyOptions.map(([code, name]) => (
                <option key={code} value={code}>{code} — {name}</option>
              ))}
            </select>
          </label>
          <button type="button" className="swap-btn" onClick={swapCurrencies} aria-label="Swap currencies" title="Swap currencies">
            ⇄
          </button>
          <label>
            To
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              {currencyOptions.map(([code, name]) => (
                <option key={code} value={code}>{code} — {name}</option>
              ))}
            </select>
          </label>
          <label className="slider-label">
            History: {days}d
            <input type="range" min="7" max="180" value={days} onChange={(e) => setDays(Number(e.target.value))} />
          </label>
          <label className="slider-label">
            Forecast: {forecastDays}d
            <input type="range" min="1" max="30" value={forecastDays} onChange={(e) => setForecastDays(Number(e.target.value))} />
          </label>
        </div>

        {base === target && <p className="error">Pick two different currencies.</p>}
        {error && <p className="error">{error}</p>}

        {loading && (
          <div className="skeleton-block">
            <div className="skeleton skeleton-summary" />
            <div className="skeleton skeleton-chart" />
          </div>
        )}

        {result && !loading && (
          <>
            <div className="summary">
              <div>
                <span className="label">Latest rate</span>
                <span className="value">1 {base} = {result.history[result.history.length - 1].rate} {target}</span>
              </div>
              <div>
                <span className="label">Trend</span>
                <span className={`value trend-badge ${trendMeta.className}`}>
                  {trendMeta.arrow} {trendMeta.label}
                  <small>{result.pct_change_forecast > 0 ? "+" : ""}{result.pct_change_forecast}%</small>
                </span>
              </div>
              <div>
                <span className="label">{forecastDays}-day forecast</span>
                <span className="value">1 {base} = {result.predictions[result.predictions.length - 1].rate} {target}</span>
              </div>
              <div>
                <span className="label">Volatility</span>
                <span className={`value volatility-badge ${result.volatility.label}`}>{result.volatility.label}</span>
              </div>
            </div>

            <div className="chart-wrap">
              <Line
                data={chartData}
                options={{
                  responsive: true,
                  plugins: { legend: { labels: { color: "#c9d1e0" } } },
                  scales: {
                    x: { ticks: { color: "#8b93a7", maxTicksLimit: 8 }, grid: { color: "rgba(255,255,255,0.05)" } },
                    y: { ticks: { color: "#8b93a7" }, grid: { color: "rgba(255,255,255,0.05)" } },
                  },
                }}
              />
            </div>
            <p className="disclaimer">{result.disclaimer}</p>

            <section className="insights-card">
              <div className="insights-tabs" role="tablist">
                {INSIGHT_TABS.map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    role="tab"
                    aria-selected={activeTab === tab.key}
                    className={`insights-tab ${activeTab === tab.key ? "active" : ""}`}
                    onClick={() => setActiveTab(tab.key)}
                  >
                    <span className="tab-icon">{tab.icon}</span> {tab.label}
                  </button>
                ))}
              </div>
              <div className="insights-panel">
                <h3>{result.insights[activeTab].stance}</h3>
                <ul>
                  {result.insights[activeTab].points.map((point, i) => (
                    <li key={i}>{point}</li>
                  ))}
                </ul>
              </div>
              <p className="disclaimer insights-disclaimer">{result.insights.disclaimer}</p>
            </section>
          </>
        )}
      </div>
    </>
  );
}

export default App;

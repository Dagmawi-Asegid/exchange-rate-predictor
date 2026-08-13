import { useMemo } from "react";
import "./MarketScene.css";

function seededRandom(seed) {
  let value = seed;
  return () => {
    value = (value * 9301 + 49297) % 233280;
    return value / 233280;
  };
}

function useCandles(trend, count = 28) {
  return useMemo(() => {
    const rand = seededRandom(trend.length * 17 + count);
    return Array.from({ length: count }, (_, i) => {
      const bullish = trend === "flat" ? rand() > 0.5 : trend === "upward" ? rand() > 0.3 : rand() > 0.7;
      return {
        id: i,
        height: 18 + rand() * 60,
        wick: 6 + rand() * 18,
        bullish,
        delay: (rand() * 4).toFixed(2),
        duration: (2.6 + rand() * 2.2).toFixed(2),
      };
    });
  }, [trend, count]);
}

function useCoins(count = 14) {
  return useMemo(() => {
    const rand = seededRandom(count * 31);
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      left: (rand() * 100).toFixed(1),
      size: 16 + rand() * 22,
      delay: (rand() * 12).toFixed(2),
      duration: (9 + rand() * 8).toFixed(2),
      symbol: ["$", "¢", "€", "£"][Math.floor(rand() * 4)],
    }));
  }, [count]);
}

export default function MarketScene({ trend = "flat", volatilityLabel = "low", tickerText = "" }) {
  const candles = useCandles(trend);
  const coins = useCoins();
  const tickerItems = tickerText ? Array(12).fill(tickerText) : [];

  return (
    <div className={`market-scene scene-${trend} vol-${volatilityLabel}`} aria-hidden="true">
      <div className="market-glow" />
      <div className="candle-row">
        {candles.map((c) => (
          <span
            key={c.id}
            className={`candle ${c.bullish ? "bull" : "bear"}`}
            style={{
              "--h": `${c.height}px`,
              "--wick": `${c.wick}px`,
              animationDelay: `${c.delay}s`,
              animationDuration: `${c.duration}s`,
            }}
          />
        ))}
      </div>
      <div className="coin-field">
        {coins.map((coin) => (
          <span
            key={coin.id}
            className="coin"
            style={{
              left: `${coin.left}%`,
              width: `${coin.size}px`,
              height: `${coin.size}px`,
              animationDelay: `${coin.delay}s`,
              animationDuration: `${coin.duration}s`,
            }}
          >
            {coin.symbol}
          </span>
        ))}
      </div>
      {tickerItems.length > 0 && (
        <div className="ticker-tape">
          <div className="ticker-track">
            {tickerItems.map((text, i) => (
              <span className="ticker-item" key={i}>
                {text}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

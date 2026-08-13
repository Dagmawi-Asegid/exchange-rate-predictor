import { useEffect, useMemo, useRef, useState } from "react";

export default function CurrencyCombobox({ id, label, currencies, value, onChange }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapRef = useRef(null);
  const inputRef = useRef(null);

  const selectedName = currencies[value] || "";

  const filtered = useMemo(() => {
    const entries = Object.entries(currencies);
    const q = query.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter(
      ([code, name]) => code.toLowerCase().includes(q) || name.toLowerCase().includes(q)
    );
  }, [query, currencies]);

  useEffect(() => {
    if (!open) return;
    const handleClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  useEffect(() => {
    setActiveIndex(-1);
  }, [query, open]);

  const selectCode = (code) => {
    onChange(code);
    setQuery("");
    setOpen(false);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e) => {
    if (!open) {
      if (e.key === "ArrowDown" || e.key === "Enter") {
        setOpen(true);
        e.preventDefault();
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pick = activeIndex >= 0 ? filtered[activeIndex] : filtered.length === 1 ? filtered[0] : null;
      if (pick) selectCode(pick[0]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
      inputRef.current?.blur();
    }
  };

  return (
    <div className="currency-combobox" ref={wrapRef}>
      <span className="field-label">{label}</span>
      <input
        ref={inputRef}
        id={id}
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={`${id}-listbox`}
        aria-autocomplete="list"
        autoComplete="off"
        className="currency-input"
        placeholder={value ? `${value} — ${selectedName}` : "Search currency…"}
        value={open ? query : ""}
        onFocus={() => setOpen(true)}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      {open && (
        <ul className="currency-dropdown" id={`${id}-listbox`} role="listbox">
          {filtered.length === 0 && <li className="currency-empty">No matches</li>}
          {filtered.slice(0, 60).map(([code, name], i) => (
            <li
              key={code}
              role="option"
              aria-selected={code === value}
              className={`currency-option ${i === activeIndex ? "active" : ""} ${code === value ? "selected" : ""}`}
              onMouseDown={(e) => {
                e.preventDefault();
                selectCode(code);
              }}
            >
              <span className="currency-code">{code}</span>
              <span className="currency-name">{name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

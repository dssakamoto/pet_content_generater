interface ThemeInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

export default function ThemeInput({ value, onChange, disabled }: ThemeInputProps) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
        <span style={{
          width: "20px",
          height: "1.5px",
          background: "var(--accent)",
          display: "inline-block",
          flexShrink: 0,
        }} />
        <label
          htmlFor="theme"
          style={{
            fontSize: "11px",
            fontWeight: 600,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "var(--accent)",
            fontFamily: "'Outfit', sans-serif",
          }}
        >
          テーマ / Theme
        </label>
      </div>
      <input
        id="theme"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="春の公園、雨の日のお昼寝..."
        style={{
          width: "100%",
          background: "transparent",
          border: "none",
          borderBottom: "2px solid var(--border)",
          padding: "10px 0",
          fontSize: "22px",
          fontFamily: "'Playfair Display', serif",
          fontWeight: 400,
          color: "var(--ink)",
          outline: "none",
          transition: "border-color 0.2s",
          opacity: disabled ? 0.5 : 1,
          boxSizing: "border-box",
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderBottomColor = "var(--accent)";
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderBottomColor = "var(--border)";
        }}
      />
    </div>
  );
}

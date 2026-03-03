interface ThemeInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}

export default function ThemeInput({ value, onChange, disabled }: ThemeInputProps) {
  return (
    <div>
      {/* <label> + htmlFor で input と紐付け (accessibility) */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
        <span style={{
          width: "3px",
          height: "12px",
          background: "var(--accent)",
          display: "inline-block",
          flexShrink: 0,
        }} />
        <label
          htmlFor="theme"
          style={{
            fontSize: "10px",
            fontWeight: 500,
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            color: "var(--ink-mid)",
            fontFamily: "'DM Sans', sans-serif",
            cursor: "pointer",
          }}
        >
          Theme
        </label>
      </div>

      <input
        id="theme"
        type="text"
        name="theme"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Spring park, rainy day nap…"
        autoComplete="off"
        aria-label="Enter a content theme"
        className="theme-input"
        style={{
          width: "100%",
          background: "transparent",
          border: "none",
          padding: "12px 0",
          fontSize: "24px",
          fontFamily: "'Cormorant Garamond', serif",
          fontWeight: 400,
          fontStyle: "italic",
          color: "var(--ink)",
          outline: "none",
          opacity: disabled ? 0.4 : 1,
          boxSizing: "border-box",
          caretColor: "var(--accent)",
        }}
      />
    </div>
  );
}

import type { Animal, OutputFormat } from "../types";

interface OutputSelectorProps {
  animal: Animal;
  format: OutputFormat;
  onAnimalChange: (animal: Animal) => void;
  onFormatChange: (format: OutputFormat) => void;
  disabled: boolean;
}

const animals: { value: Animal; label: string; icon: string }[] = [
  { value: "cat", label: "猫", icon: "🐱" },
  { value: "dog", label: "犬", icon: "🐶" },
  { value: "random", label: "おまかせ", icon: "✦" },
];

const formats: { value: OutputFormat; label: string; icon: string }[] = [
  { value: "image", label: "画像", icon: "◻" },
  { value: "video", label: "動画", icon: "▷" },
];

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
      <span style={{
        width: "20px",
        height: "1.5px",
        background: "var(--accent)",
        display: "inline-block",
        flexShrink: 0,
      }} />
      <span style={{
        fontSize: "11px",
        fontWeight: 600,
        letterSpacing: "0.18em",
        textTransform: "uppercase",
        color: "var(--accent)",
        fontFamily: "'Outfit', sans-serif",
      }}>
        {children}
      </span>
    </div>
  );
}

function StampToggle<T extends string>({
  options,
  value,
  onChange,
  disabled,
}: {
  options: { value: T; label: string; icon: string }[];
  value: T;
  onChange: (v: T) => void;
  disabled: boolean;
}) {
  return (
    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          className="stamp-btn"
          style={value === opt.value ? {
            background: "var(--accent)",
            borderColor: "var(--accent)",
            color: "white",
            boxShadow: "2px 2px 0 var(--accent-dark)",
          } : {}}
        >
          <span style={{ marginRight: "5px" }}>{opt.icon}</span>
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export default function OutputSelector({
  animal,
  format,
  onAnimalChange,
  onFormatChange,
  disabled,
}: OutputSelectorProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      <div>
        <SectionLabel>動物 / Animal</SectionLabel>
        <StampToggle
          options={animals}
          value={animal}
          onChange={onAnimalChange}
          disabled={disabled}
        />
      </div>
      <div>
        <SectionLabel>出力形式 / Format</SectionLabel>
        <StampToggle
          options={formats}
          value={format}
          onChange={onFormatChange}
          disabled={disabled}
        />
      </div>
    </div>
  );
}

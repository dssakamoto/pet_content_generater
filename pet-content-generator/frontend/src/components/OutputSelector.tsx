import { memo } from "react";
import type { Animal, OutputFormat } from "../types";

interface OutputSelectorProps {
  animal: Animal;
  format: OutputFormat;
  onAnimalChange: (animal: Animal) => void;
  onFormatChange: (format: OutputFormat) => void;
  disabled: boolean;
}

const animals: { value: Animal; label: string; icon: string }[] = [
  { value: "cat", label: "Cat", icon: "🐱" },
  { value: "dog", label: "Dog", icon: "🐶" },
  { value: "random", label: "Random", icon: "✦" },
];

const formats: { value: OutputFormat; label: string; icon: string }[] = [
  { value: "image", label: "Image", icon: "◻" },
  { value: "video", label: "Video", icon: "▷" },
];

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
      <span style={{
        width: "3px",
        height: "12px",
        background: "var(--accent)",
        display: "inline-block",
        flexShrink: 0,
      }} />
      <span style={{
        fontSize: "10px",
        fontWeight: 500,
        letterSpacing: "0.2em",
        textTransform: "uppercase",
        color: "var(--ink-mid)",
        fontFamily: "'DM Sans', sans-serif",
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
  groupLabel,
}: {
  options: { value: T; label: string; icon: string }[];
  value: T;
  onChange: (v: T) => void;
  disabled: boolean;
  groupLabel: string;
}) {
  return (
    /* role="group" + aria-label でスクリーンリーダー向けにグループを明示 */
    <div role="group" aria-label={groupLabel} style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          aria-pressed={value === opt.value}
          className="stamp-btn"
          style={value === opt.value ? {
            background: "var(--accent)",
            borderColor: "var(--accent)",
            color: "#1A1410",
            boxShadow: "0 2px 8px rgba(196, 154, 40, 0.3)",
            fontWeight: 600,
          } : {}}
        >
          <span aria-hidden="true" style={{ marginRight: "5px" }}>{opt.icon}</span>
          {opt.label}
        </button>
      ))}
    </div>
  );
}

const OutputSelector = memo(function OutputSelector({
  animal,
  format,
  onAnimalChange,
  onFormatChange,
  disabled,
}: OutputSelectorProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <div>
        <SectionLabel>Animal</SectionLabel>
        <StampToggle
          options={animals}
          value={animal}
          onChange={onAnimalChange}
          disabled={disabled}
          groupLabel="Select animal type"
        />
      </div>
      <div>
        <SectionLabel>Format</SectionLabel>
        <StampToggle
          options={formats}
          value={format}
          onChange={onFormatChange}
          disabled={disabled}
          groupLabel="Select output format"
        />
      </div>
    </div>
  );
});

export default OutputSelector;

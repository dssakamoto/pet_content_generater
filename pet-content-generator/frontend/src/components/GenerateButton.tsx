import { memo } from "react";

interface GenerateButtonProps {
  onClick: () => void;
  loading: boolean;
  disabled: boolean;
  label: string;
}

const GenerateButton = memo(function GenerateButton({
  onClick,
  loading,
  disabled,
  label,
}: GenerateButtonProps) {
  const isInactive = disabled || loading;

  return (
    <div>
      <div style={{ height: "1px", background: "var(--border)", marginBottom: "36px" }} />
      <button
        type="button"
        onClick={onClick}
        disabled={isInactive}
        /* aria-busy: スクリーンリーダーにビジー状態を伝える */
        aria-busy={loading}
        aria-label={loading ? "Generating…" : label}
        style={{
          width: "100%",
          padding: "20px 32px",
          background: isInactive
            ? "var(--border-light)"
            : "var(--accent)",
          color: isInactive ? "var(--ink-dim)" : "#1A1410",
          border: "none",
          fontSize: "12px",
          fontFamily: "'DM Sans', sans-serif",
          fontWeight: 600,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          cursor: isInactive ? "not-allowed" : "pointer",
          /* explicit transition properties — not "all" */
          transition: "background-color 0.15s ease, color 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease",
          borderRadius: "2px",
          boxShadow: isInactive ? "none" : "0 4px 20px rgba(196, 154, 40, 0.25)",
          transform: "translateY(0)",
          touchAction: "manipulation",
        }}
        onMouseEnter={(e) => {
          if (!isInactive) {
            e.currentTarget.style.background = "var(--accent-hover)";
            e.currentTarget.style.boxShadow = "0 6px 28px rgba(196, 154, 40, 0.35)";
            e.currentTarget.style.transform = "translateY(-1px)";
          }
        }}
        onMouseLeave={(e) => {
          if (!isInactive) {
            e.currentTarget.style.background = "var(--accent)";
            e.currentTarget.style.boxShadow = "0 4px 20px rgba(196, 154, 40, 0.25)";
            e.currentTarget.style.transform = "translateY(0)";
          }
        }}
        onMouseDown={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translateY(1px)";
            e.currentTarget.style.boxShadow = "0 2px 10px rgba(196, 154, 40, 0.2)";
          }
        }}
        onMouseUp={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = "0 6px 28px rgba(196, 154, 40, 0.35)";
          }
        }}
      >
        {loading ? (
          <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}>
            {/* aria-hidden: スピナーはvisualのみ、テキストで状態を伝える */}
            <span
              aria-hidden="true"
              style={{
                width: "13px",
                height: "13px",
                border: "1.5px solid rgba(26, 20, 16, 0.3)",
                borderTopColor: "#1A1410",
                borderRadius: "50%",
                display: "inline-block",
                animation: "spin 0.8s linear infinite",
              }}
            />
            Generating…
          </span>
        ) : label}
      </button>
    </div>
  );
});

export default GenerateButton;

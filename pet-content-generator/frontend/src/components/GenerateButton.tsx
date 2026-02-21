interface GenerateButtonProps {
  onClick: () => void;
  loading: boolean;
  disabled: boolean;
  label: string;
}

export default function GenerateButton({
  onClick,
  loading,
  disabled,
  label,
}: GenerateButtonProps) {
  const isInactive = disabled || loading;

  return (
    <div>
      <div style={{ height: "1px", background: "var(--border)", marginBottom: "32px" }} />
      <button
        type="button"
        onClick={onClick}
        disabled={isInactive}
        style={{
          width: "100%",
          padding: "18px 32px",
          background: isInactive ? "var(--border)" : "var(--accent)",
          color: isInactive ? "var(--ink-light)" : "white",
          border: "none",
          fontSize: "13px",
          fontFamily: "'Outfit', sans-serif",
          fontWeight: 600,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          cursor: isInactive ? "not-allowed" : "pointer",
          transition: "all 0.15s ease",
          boxShadow: isInactive ? "none" : "3px 3px 0 var(--accent-dark)",
          transform: "translate(0, 0)",
          borderRadius: "2px",
        }}
        onMouseEnter={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translate(-1px, -1px)";
            e.currentTarget.style.boxShadow = "4px 4px 0 var(--accent-dark)";
          }
        }}
        onMouseLeave={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translate(0, 0)";
            e.currentTarget.style.boxShadow = "3px 3px 0 var(--accent-dark)";
          }
        }}
        onMouseDown={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translate(2px, 2px)";
            e.currentTarget.style.boxShadow = "1px 1px 0 var(--accent-dark)";
          }
        }}
        onMouseUp={(e) => {
          if (!isInactive) {
            e.currentTarget.style.transform = "translate(-1px, -1px)";
            e.currentTarget.style.boxShadow = "4px 4px 0 var(--accent-dark)";
          }
        }}
      >
        {loading ? (
          <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "10px" }}>
            <span style={{
              width: "14px",
              height: "14px",
              border: "2px solid rgba(100, 70, 40, 0.3)",
              borderTopColor: "var(--ink-mid)",
              borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.8s linear infinite",
            }} />
            生成中...
          </span>
        ) : label}
      </button>
    </div>
  );
}

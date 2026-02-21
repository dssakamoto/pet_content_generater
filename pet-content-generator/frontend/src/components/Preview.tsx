import type { GenerateResult } from "../types";

interface PreviewProps {
  result: GenerateResult | null;
}

function downloadFile(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function ResultHeader() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "28px" }}>
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
        生成結果 / Result
      </span>
    </div>
  );
}

function SaveButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        background: "none",
        border: "none",
        fontSize: "10px",
        color: "var(--ink-mid)",
        cursor: "pointer",
        fontFamily: "'Outfit', sans-serif",
        fontWeight: 500,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        padding: 0,
        textDecoration: "underline",
        textDecorationColor: "var(--border)",
        textUnderlineOffset: "3px",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = "var(--accent)";
        e.currentTarget.style.textDecorationColor = "var(--accent)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = "var(--ink-mid)";
        e.currentTarget.style.textDecorationColor = "var(--border)";
      }}
    >
      Save
    </button>
  );
}

export default function Preview({ result }: PreviewProps) {
  if (!result) return null;

  if (result.type === "image" && result.images) {
    return (
      <div style={{ paddingTop: "8px" }}>
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "32px" }} />
        <ResultHeader />
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "28px",
        }}>
          {result.images.map((src, i) => (
            <div
              key={i}
              className="polaroid"
              style={{ transform: `rotate(${i % 2 === 0 ? -1.5 : 1}deg)` }}
            >
              <img
                src={src}
                alt={`Generated ${i + 1}`}
                style={{ width: "100%", display: "block" }}
              />
              <div style={{
                paddingTop: "10px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <span style={{
                  fontSize: "10px",
                  color: "var(--ink-light)",
                  fontFamily: "'Outfit', sans-serif",
                  fontWeight: 300,
                  letterSpacing: "0.05em",
                }}>
                  No.{String(i + 1).padStart(2, "0")}
                </span>
                <SaveButton onClick={() => downloadFile(src, `pet-${i + 1}.png`)} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (result.type === "video" && result.video) {
    return (
      <div style={{ paddingTop: "8px" }}>
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "32px" }} />
        <ResultHeader />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "20px" }}>
          <div
            className="polaroid"
            style={{ width: "100%", maxWidth: "280px", transform: "rotate(-0.5deg)" }}
          >
            <video
              src={result.video}
              controls
              style={{ width: "100%", display: "block", aspectRatio: "9/16" }}
            />
            <div style={{
              paddingTop: "12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}>
              <span style={{
                fontSize: "10px",
                color: "var(--ink-light)",
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 300,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}>
                Video
              </span>
              <SaveButton onClick={() => downloadFile(result.video!, "pet-video.mp4")} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

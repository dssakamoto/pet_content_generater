import { memo } from "react";
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
    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "32px" }}>
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
        Result
      </span>
    </div>
  );
}

function SaveButton({ onClick, filename }: { onClick: () => void; filename: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Download ${filename}`}
      style={{
        background: "none",
        border: "none",
        fontSize: "9px",
        color: "#9A8A70",
        cursor: "pointer",
        fontFamily: "'DM Sans', sans-serif",
        fontWeight: 500,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        padding: 0,
        textDecoration: "underline",
        textDecorationColor: "#D4C8B0",
        textUnderlineOffset: "3px",
        /* explicit transition */
        transition: "color 0.15s ease, text-decoration-color 0.15s ease",
        touchAction: "manipulation",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = "#6A5C40";
        e.currentTarget.style.textDecorationColor = "#6A5C40";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = "#9A8A70";
        e.currentTarget.style.textDecorationColor = "#D4C8B0";
      }}
    >
      Save
    </button>
  );
}

const Preview = memo(function Preview({ result }: PreviewProps) {
  if (result === null) return null;

  if (result.type === "image" && result.images) {
    return (
      <section aria-label="Generated images" style={{ paddingTop: "8px" }}>
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "36px" }} />
        <ResultHeader />
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "32px",
        }}>
          {result.images.map((src, i) => (
            <div
              key={src}
              className="polaroid"
              style={{ transform: `rotate(${i % 2 === 0 ? -1.8 : 1.2}deg)` }}
            >
              <img
                src={src}
                alt={`Generated image ${i + 1}`}
                /* width/height で CLS を防止 (生成サイズ 1080x1080) */
                width={1080}
                height={1080}
                /* below-fold は lazy load */
                loading={i < 2 ? "eager" : "lazy"}
                style={{ width: "100%", height: "auto", display: "block" }}
              />
              <div style={{
                paddingTop: "10px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <span style={{
                  fontSize: "9px",
                  color: "#9A8A70",
                  fontFamily: "'DM Sans', sans-serif",
                  fontWeight: 300,
                  letterSpacing: "0.06em",
                  /* tabular-nums で番号を等幅に */
                  fontVariantNumeric: "tabular-nums",
                }}>
                  No.{String(i + 1).padStart(2, "0")}
                </span>
                <SaveButton
                  onClick={() => downloadFile(src, `pet-${i + 1}.png`)}
                  filename={`pet-${i + 1}.png`}
                />
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (result.type === "video" && result.video) {
    return (
      <section aria-label="Generated video" style={{ paddingTop: "8px" }}>
        <div style={{ height: "1px", background: "var(--border)", marginBottom: "36px" }} />
        <ResultHeader />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
          <div
            className="polaroid"
            style={{ width: "100%", maxWidth: "260px", transform: "rotate(-0.8deg)" }}
          >
            <video
              src={result.video}
              controls
              style={{ width: "100%", display: "block", aspectRatio: "9/16" }}
              aria-label="Generated pet video"
            />
            <div style={{
              paddingTop: "12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}>
              <span style={{
                fontSize: "9px",
                color: "#9A8A70",
                fontFamily: "'DM Sans', sans-serif",
                fontWeight: 300,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}>
                Video
              </span>
              <SaveButton
                onClick={() => downloadFile(result.video!, "pet-video.mp4")}
                filename="pet-video.mp4"
              />
            </div>
          </div>
        </div>
      </section>
    );
  }

  return null;
});

export default Preview;

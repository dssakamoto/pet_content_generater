import { useState, useCallback } from "react";
import ThemeInput from "./components/ThemeInput";
import OutputSelector from "./components/OutputSelector";
import GenerateButton from "./components/GenerateButton";
import Preview from "./components/Preview";
import { generateImage, generateVideo } from "./api/client";
import type { Animal, OutputFormat, GenerateResult } from "./types";

export default function App() {
  const [theme, setTheme] = useState("");
  const [animal, setAnimal] = useState<Animal>("cat");
  const [format, setFormat] = useState<OutputFormat>("image");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(async () => {
    if (!theme.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      if (format === "image") {
        const res = await generateImage(theme, animal);
        setResult({ type: "image", images: res.images });
      } else {
        const res = await generateVideo(theme, animal);
        setResult({ type: "video", video: res.video });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }, [theme, animal, format]);

  const label = format === "image" ? "Generate Image" : "Generate Video";
  const isDisabled = !theme.trim();

  return (
    <div style={{ minHeight: "100vh", paddingBottom: "80px" }}>
      <div style={{ maxWidth: "600px", margin: "0 auto", padding: "0 24px" }}>

        <header style={{ paddingTop: "72px", paddingBottom: "56px" }}>
          {/* Studio badge */}
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            border: "1px solid var(--border-light)",
            color: "var(--ink-mid)",
            fontSize: "10px",
            fontWeight: 500,
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            padding: "5px 12px",
            marginBottom: "28px",
            fontFamily: "'DM Sans', sans-serif",
          }}>
            <span style={{ color: "var(--accent)", fontSize: "8px" }}>◆</span>
            AI Studio
          </div>

          {/* Title — text-wrap: balance prevents widow lines */}
          <h1 style={{
            fontFamily: "'Cormorant Garamond', serif",
            fontSize: "clamp(48px, 9vw, 72px)",
            fontWeight: 600,
            lineHeight: 1.0,
            margin: "0 0 20px",
            color: "var(--ink)",
            letterSpacing: "-0.02em",
            textWrap: "balance",
          } as React.CSSProperties}>
            Pet Content
            <br />
            <em style={{
              fontStyle: "italic",
              fontWeight: 300,
              color: "var(--accent)",
            }}>
              Generator
            </em>
          </h1>

          <p style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "14px",
            color: "var(--ink-mid)",
            margin: 0,
            fontWeight: 300,
            letterSpacing: "0.03em",
          }}>
            Enter a theme and create adorable pet content
          </p>

          {/* Gold gradient rule */}
          <div style={{
            height: "1px",
            background: "linear-gradient(90deg, var(--accent) 0%, var(--border-light) 40%, transparent 100%)",
            marginTop: "36px",
            opacity: 0.7,
          }} />
        </header>

        {/* id="main" for skip-link target */}
        <main id="main" style={{ display: "flex", flexDirection: "column", gap: "44px" }}>
          <ThemeInput value={theme} onChange={setTheme} disabled={loading} />
          <OutputSelector
            animal={animal}
            format={format}
            onAnimalChange={setAnimal}
            onFormatChange={setFormat}
            disabled={loading}
          />
          <GenerateButton
            onClick={handleGenerate}
            loading={loading}
            disabled={isDisabled}
            label={label}
          />

          {/* aria-live: screen readers announce errors automatically */}
          <div aria-live="polite" aria-atomic="true">
            {error ? (
              <div role="alert" style={{
                padding: "12px 16px",
                background: "rgba(196, 154, 40, 0.08)",
                border: "1px solid rgba(196, 154, 40, 0.25)",
                borderRadius: "2px",
                color: "var(--ink-mid)",
                fontSize: "13px",
                fontFamily: "'DM Sans', sans-serif",
                lineHeight: 1.6,
              }}>
                ⚠ {error}
              </div>
            ) : null}
          </div>

          <Preview result={result} />
        </main>

      </div>
    </div>
  );
}

import { useState } from "react";
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

  const handleGenerate = async () => {
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
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", paddingBottom: "80px" }}>
      <div style={{ maxWidth: "600px", margin: "0 auto", padding: "0 24px" }}>

        {/* ヘッダー */}
        <header style={{ paddingTop: "64px", paddingBottom: "48px" }}>
          <div style={{
            display: "inline-block",
            border: "1.5px solid var(--accent)",
            color: "var(--accent)",
            fontSize: "10px",
            fontWeight: 600,
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            padding: "4px 10px",
            marginBottom: "20px",
            fontFamily: "'Outfit', sans-serif",
          }}>
            ✦ AI Studio
          </div>
          <h1 style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: "clamp(42px, 8vw, 64px)",
            fontWeight: 700,
            lineHeight: 1.05,
            margin: "0 0 16px",
            color: "var(--ink)",
            letterSpacing: "-0.02em",
          }}>
            Pet Content<br />
            <em style={{ fontStyle: "italic", color: "var(--accent)" }}>Generator</em>
          </h1>
          <p style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: "15px",
            color: "var(--ink-mid)",
            margin: 0,
            fontWeight: 300,
            letterSpacing: "0.02em",
          }}>
            テーマを入力して、癒し系コンテンツをつくろう
          </p>
          <div style={{
            height: "1px",
            background: "linear-gradient(90deg, var(--accent) 0%, var(--border) 50%, transparent 100%)",
            marginTop: "32px",
          }} />
        </header>

        {/* フォーム */}
        <div style={{ display: "flex", flexDirection: "column", gap: "40px" }}>
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
            disabled={!theme.trim()}
            label={format === "image" ? "画像を生成" : "動画を生成"}
          />
          {error && (
            <div style={{
              padding: "12px 16px",
              background: "#FFF0EC",
              border: "1px solid #F0C0B0",
              borderRadius: "2px",
              color: "var(--accent-dark)",
              fontSize: "14px",
              fontFamily: "'Outfit', sans-serif",
            }}>
              {error}
            </div>
          )}
          <Preview result={result} />
        </div>

      </div>
    </div>
  );
}

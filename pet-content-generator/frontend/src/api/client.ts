import type {
  Animal,
  ImageResponse,
  VideoResponse,
} from "../types";

const API_BASE = "/api";

export async function generateImage(
  theme: string,
  animal: Animal,
  count: number = 4
): Promise<ImageResponse> {
  const res = await fetch(`${API_BASE}/generate/image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, animal, count }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to generate image");
  }
  return res.json();
}

export async function generateVideo(
  theme: string,
  animal: Animal
): Promise<VideoResponse> {
  const res = await fetch(`${API_BASE}/generate/video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, animal }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to generate video");
  }
  return res.json();
}

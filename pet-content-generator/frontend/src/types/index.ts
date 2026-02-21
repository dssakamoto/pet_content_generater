export type Animal = "cat" | "dog" | "random";
export type OutputFormat = "image" | "video";

export interface GenerateImageRequest {
  theme: string;
  animal: Animal;
  count: number;
}

export interface GenerateVideoRequest {
  theme: string;
  animal: Animal;
}

export interface ImageResponse {
  images: string[];
}

export interface VideoResponse {
  video: string;
}

export interface GenerateResult {
  type: OutputFormat;
  images?: string[];
  video?: string;
}

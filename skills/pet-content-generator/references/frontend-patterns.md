# Frontend Patterns Reference

## Table of Contents
- [Project Structure](#project-structure)
- [TypeScript Types](#typescript-types)
- [API Client](#api-client)
- [App Container Component](#app-container-component)
- [Component Patterns](#component-patterns)
- [Vite + Proxy Configuration](#vite--proxy-configuration)
- [Dockerfile](#dockerfile)
- [TailwindCSS Setup](#tailwindcss-setup)

## Project Structure

```
frontend/
├── Dockerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── vite-env.d.ts
    ├── components/
    │   ├── ThemeInput.tsx
    │   ├── OutputSelector.tsx
    │   ├── GenerateButton.tsx
    │   └── Preview.tsx
    ├── api/
    │   └── client.ts
    └── types/
        └── index.ts
```

## TypeScript Types

```typescript
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
```

## API Client

Fetch-based, no external HTTP library:

```typescript
const API_BASE = "/api";

export async function generateImage(theme, animal, count = 4): Promise<ImageResponse> {
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
```

- Uses relative `/api` path (resolved by Vite proxy in dev)
- Error handling: tries to parse FastAPI error detail, falls back to generic message

## App Container Component

Single container with React `useState` hooks:

```typescript
const [theme, setTheme] = useState("");
const [animal, setAnimal] = useState<Animal>("cat");
const [format, setFormat] = useState<OutputFormat>("image");
const [loading, setLoading] = useState(false);
const [result, setResult] = useState<GenerateResult | null>(null);
const [error, setError] = useState<string | null>(null);
```

State flow in `handleGenerate()`:
1. Validate theme non-empty
2. Set `loading=true`, clear error and result
3. Call API based on format selection
4. Set result or error
5. Set `loading=false` in finally block

No external state management (Redux/Zustand). Props drilled to child components.

## Component Patterns

### ThemeInput
- Controlled text input with Japanese label and placeholder
- Props: `value`, `onChange`, `disabled`
- Pink focus ring for brand consistency

### OutputSelector
- Generic `ToggleGroup<T>` component reused for animal and format selection
- Active state: pink background. Inactive: white with border + hover effect
- Responsive: column on mobile, row on desktop (`flex-col sm:flex-row`)

### GenerateButton
- Gradient button (pink→purple) with shadow
- Loading state: animated SVG spinner + "生成中..." text
- Disabled when theme is empty or loading

### Preview
- Conditional rendering based on `result.type`
- Image mode: 2-column grid, hover-reveal download buttons per image
- Video mode: 9:16 aspect ratio `<video>` player with download button
- Download via temporary `<a>` element click

## Vite + Proxy Configuration

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": { target: "http://backend:8000", changeOrigin: true },
      "/outputs": { target: "http://backend:8000", changeOrigin: true },
    },
  },
});
```

- `host: "0.0.0.0"` required for Docker container access
- Proxy uses Docker service name `backend` for container-to-container networking
- Both `/api` and `/outputs` proxied to backend

## Dockerfile

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

- `package-lock.json*` glob allows build without lock file
- Vite host configured in vite.config.ts, not CLI args

## TailwindCSS Setup

Three config files required:
- `tailwind.config.js`: content paths for `index.html` + `src/**/*.{js,ts,jsx,tsx}`
- `postcss.config.js`: tailwindcss + autoprefixer plugins
- `src/index.css`: `@tailwind base/components/utilities` directives

Design system:
- Background: `bg-gradient-to-br from-pink-50 via-white to-purple-50`
- Cards: `bg-white rounded-2xl shadow-lg p-6`
- Primary actions: `bg-gradient-to-r from-pink-400 to-purple-400` (buttons)
- Accent: `focus:border-pink-400 focus:ring-pink-200` (inputs)
- Japanese UI text throughout

## Dependencies

```json
{
  "react": "^18.3.1",
  "react-dom": "^18.3.1",
  "@vitejs/plugin-react": "^4.3.4",
  "tailwindcss": "^3.4.17",
  "typescript": "^5.7.3",
  "vite": "^6.0.7"
}
```

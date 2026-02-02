import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import path from "path";

const UI_APPS = [
  "pods",
  "logs",
  "deployments",
  "helm",
  "cluster",
  "cost",
  "events",
  "network",
] as const;

export default defineConfig(({ mode }) => {
  const uiApp = process.env.UI_APP || "pods";

  if (!UI_APPS.includes(uiApp as (typeof UI_APPS)[number])) {
    throw new Error(
      `Invalid UI_APP: ${uiApp}. Must be one of: ${UI_APPS.join(", ")}`
    );
  }

  return {
    plugins: [react(), viteSingleFile()],
    root: path.resolve(__dirname, `src/ui/${uiApp}`),
    build: {
      sourcemap: mode === "development" ? "inline" : false,
      cssMinify: mode !== "development",
      minify: mode !== "development",
      outDir: path.resolve(__dirname, "dist/ui"),
      emptyOutDir: false,
      rollupOptions: {
        input: path.resolve(__dirname, `src/ui/${uiApp}/mcp-app.html`),
        output: {
          entryFileNames: `${uiApp}.js`,
          assetFileNames: `${uiApp}.[ext]`,
        },
      },
    },
    resolve: {
      alias: {
        "@shared": path.resolve(__dirname, "src/ui/shared"),
      },
    },
  };
});

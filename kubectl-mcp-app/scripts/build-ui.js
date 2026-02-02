#!/usr/bin/env node

import { execSync } from "child_process";
import { mkdirSync, existsSync, renameSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, "..");

const UI_APPS = [
  "pods",
  "logs",
  "deployments",
  "helm",
  "cluster",
  "cost",
  "events",
  "network",
];

const distDir = join(rootDir, "dist", "ui");

if (!existsSync(distDir)) {
  mkdirSync(distDir, { recursive: true });
}

console.log("Building UI apps...\n");

for (const app of UI_APPS) {
  console.log(`Building ${app}...`);

  try {
    execSync(`npx vite build`, {
      cwd: rootDir,
      stdio: "inherit",
      env: { ...process.env, UI_APP: app },
    });

    const sourceFile = join(distDir, "mcp-app.html");
    const targetFile = join(distDir, `${app}.html`);

    if (existsSync(sourceFile)) {
      renameSync(sourceFile, targetFile);
      console.log(`  -> ${app}.html created\n`);
    } else {
      console.log(`  -> Warning: mcp-app.html not found for ${app}\n`);
    }
  } catch (error) {
    console.error(`  -> Error building ${app}:`, error.message);
    process.exit(1);
  }
}

console.log("\nAll UI apps built successfully!");
console.log(`Output directory: ${distDir}`);

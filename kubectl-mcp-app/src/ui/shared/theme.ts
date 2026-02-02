export type Theme = "dark" | "light";

export interface ThemeColors {
  bg: string;
  bgSecondary: string;
  bgTertiary: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  border: string;
  borderHover: string;
  primary: string;
  primaryHover: string;
  success: string;
  successBg: string;
  warning: string;
  warningBg: string;
  error: string;
  errorBg: string;
  info: string;
  infoBg: string;
}

export const darkTheme: ThemeColors = {
  bg: "#0d1117",
  bgSecondary: "#161b22",
  bgTertiary: "#21262d",
  text: "#e6edf3",
  textSecondary: "#8b949e",
  textMuted: "#484f58",
  border: "#30363d",
  borderHover: "#484f58",
  primary: "#2f81f7",
  primaryHover: "#388bfd",
  success: "#3fb950",
  successBg: "rgba(63, 185, 80, 0.15)",
  warning: "#d29922",
  warningBg: "rgba(210, 153, 34, 0.15)",
  error: "#f85149",
  errorBg: "rgba(248, 81, 73, 0.15)",
  info: "#58a6ff",
  infoBg: "rgba(88, 166, 255, 0.15)",
};

export const lightTheme: ThemeColors = {
  bg: "#ffffff",
  bgSecondary: "#f6f8fa",
  bgTertiary: "#eaeef2",
  text: "#1f2328",
  textSecondary: "#656d76",
  textMuted: "#8c959f",
  border: "#d0d7de",
  borderHover: "#8c959f",
  primary: "#0969da",
  primaryHover: "#0550ae",
  success: "#1a7f37",
  successBg: "rgba(26, 127, 55, 0.1)",
  warning: "#9a6700",
  warningBg: "rgba(154, 103, 0, 0.1)",
  error: "#cf222e",
  errorBg: "rgba(207, 34, 46, 0.1)",
  info: "#0969da",
  infoBg: "rgba(9, 105, 218, 0.1)",
};

export function getTheme(): Theme {
  if (typeof window === "undefined") return "dark";

  const stored = localStorage.getItem("k8s-ui-theme");
  if (stored === "light" || stored === "dark") return stored;

  return window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

export function setTheme(theme: Theme): void {
  localStorage.setItem("k8s-ui-theme", theme);
  document.documentElement.setAttribute("data-theme", theme);
}

export function getColors(theme: Theme = getTheme()): ThemeColors {
  return theme === "light" ? lightTheme : darkTheme;
}

export function generateCssVariables(colors: ThemeColors): string {
  return Object.entries(colors)
    .map(([key, value]) => `--${camelToKebab(key)}: ${value};`)
    .join("\n  ");
}

function camelToKebab(str: string): string {
  return str.replace(/([a-z])([A-Z])/g, "$1-$2").toLowerCase();
}

export const baseStyles = `
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :root {
    ${generateCssVariables(darkTheme)}
  }

  [data-theme="light"] {
    ${generateCssVariables(lightTheme)}
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a {
    color: var(--primary);
    text-decoration: none;
  }

  a:hover {
    text-decoration: underline;
  }

  button {
    font-family: inherit;
    font-size: inherit;
    cursor: pointer;
  }

  input, select, textarea {
    font-family: inherit;
    font-size: inherit;
  }

  code, pre {
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    font-size: 12px;
  }

  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--bg-secondary);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--border-hover);
  }
`;

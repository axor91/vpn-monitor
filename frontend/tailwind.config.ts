import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#09090b", card: "#111113", hover: "#18181b" },
        border: { DEFAULT: "#27272a", hover: "#3f3f46" },
        accent: { DEFAULT: "#7c3aed", light: "#a78bfa", dim: "#7c3aed20" },
        success: { DEFAULT: "#22c55e", dim: "#22c55e20" },
        danger: { DEFAULT: "#ef4444", dim: "#ef444420" },
        warn: { DEFAULT: "#f59e0b", dim: "#f59e0b20" },
        muted: "#71717a",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "fade-in": "fadeIn 0.2s ease-out",
      },
      keyframes: {
        slideIn: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

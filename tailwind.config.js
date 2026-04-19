// tailwind.config.js — Tailwind CSS configuration for Lumara
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Lumara dark-room palette
        surface: {
          DEFAULT: "#1a1a1a",
          elevated: "#242424",
          overlay: "#2e2e2e",
        },
        accent: {
          DEFAULT: "#f5a623",
          dim: "#c47d0e",
        },
        muted: "#6b6b6b",
        border: "#333333",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

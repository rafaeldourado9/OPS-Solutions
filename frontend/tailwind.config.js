/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        teal: { DEFAULT: "#0ABAB5", dark: "#089B97" },
        navy: "#0A1628",
        dark: { DEFAULT: "#111111", card: "#1A1A1E", hover: "#222228" },
        "gray-bg": "#F5F5F7",
        "gray-text": "#86868B",
        "gray-light": "#A1A1A6",
        text: { primary: "#1D1D1F" },
      },
      fontFamily: {
        sans: ["Outfit", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "#e5e7eb",
        surface: "#f8fafc",
        ink: "#101828",
        muted: "#667085",
        accent: "#2563eb",
      },
      boxShadow: {
        soft: "0 18px 48px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

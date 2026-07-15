/** @type {import('tailwindcss').Config} */

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      colors: {
        bg: "#F8F9FB",
        surface: "#FFFFFF",
        ink: "#1E1E2E",
        blue: {
          DEFAULT: "#2563EB",
          dim: "rgba(37, 99, 235, 0.16)",
          border: "rgba(37, 99, 235, 0.35)",
          focus: "rgba(37, 99, 235, 0.08)",
        },
        purple: {
          DEFAULT: "#7C6FE3",
          dim: "rgba(124, 111, 227, 0.10)",
          muted: "rgba(124, 111, 227, 0.80)",
        },
        pink: {
          DEFAULT: "#F472B6",
          dim: "rgba(244, 114, 182, 0.10)",
          border: "rgba(244, 114, 182, 0.30)",
        },
        border: {
          DEFAULT: "rgba(30, 30, 46, 0.10)",
          hover: "rgba(30, 30, 46, 0.18)",
        },
        text: {
          primary: "#1E1E2E",
          secondary: "rgba(30, 30, 46, 0.70)",
          tertiary: "rgba(30, 30, 46, 0.46)",
        },
        status: {
          "completed-bg": "#dcfce7",
          "completed-text": "#15803d",
          "completed-border": "#86efac",
          "failed-bg": "#fce7f3",
          "failed-text": "#be185d",
          "failed-border": "#f9a8d4",
          "running-bg": "#eff6ff",
          "running-text": "#1d4ed8",
          "running-border": "#93c5fd",
          "queued-bg": "#f5f3ff",
          "queued-text": "#6d28d9",
          "queued-border": "#c4b5fd",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["DM Mono", "monospace"],
      },
      boxShadow: {
        card: "0 10px 30px rgba(30, 30, 46, 0.06)",
        modal: "0 20px 60px rgba(30, 30, 46, 0.20)",
      },
      borderRadius: {
        card: "12px",
        inner: "8px",
        badge: "20px",
        pill: "24px",
      },
      backgroundImage: {
        brand: "linear-gradient(135deg, #2563EB 0%, #7C6FE3 65%, #F472B6 100%)",
        "brand-h": "linear-gradient(90deg, #2563EB 0%, #7C6FE3 65%, #F472B6 100%)",
      },
    },
  },
  plugins: [],
};

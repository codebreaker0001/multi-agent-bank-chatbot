/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      colors: {
        // Deep navy/charcoal primary — sidebar, headings, primary buttons
        navy: {
          50: "#f5f6f8",
          100: "#e8eaee",
          200: "#d3d7e0",
          300: "#aab0c0",
          400: "#5b6478",
          500: "#454e63",
          600: "#333c50",
          700: "#242c3d",
          800: "#161c2b",
          900: "#0d111c",
        },
        // Sophisticated single accent — used sparingly for focus/active states
        accent: {
          50: "#eef4ff",
          100: "#dbe7ff",
          500: "#3b5bdb",
          600: "#2f4bc0",
        },
        positive: { DEFAULT: "#1a9c5b", bg: "#eafaf1" },
        negative: { DEFAULT: "#d6483f", bg: "#fdecea" },
        warning: { DEFAULT: "#b3791d", bg: "#fdf3e2" },
      },
      boxShadow: {
        card: "0 1px 2px rgba(13,17,28,0.04), 0 4px 16px rgba(13,17,28,0.06)",
        elevated: "0 8px 30px rgba(13,17,28,0.10)",
      },
      borderRadius: {
        xl2: "18px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

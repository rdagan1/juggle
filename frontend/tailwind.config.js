/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Rubik", "system-ui", "sans-serif"],
      },
      colors: {
        gio: {
          50: "#eef2ff",
          100: "#dde6ff",
          500: "#4f73f5",
          600: "#3d5ce0",
          700: "#2e47c4",
        },
        navy: {
          50: "#f0f4ff",
          100: "#dde6ff",
          200: "#b8caf5",
          800: "#0f2040",
          900: "#0a1628",
        },
        urgent: "#ef4444",
        "urgent-bg": "#fef2f2",
      },
    },
  },
  safelist: ["bg-navy-50", "bg-navy-100", "bg-navy-800", "bg-navy-900", "text-navy-200", "border-navy-100", "border-navy-200", "divide-navy-50"],
  plugins: [],
};

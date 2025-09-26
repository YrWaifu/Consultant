/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/app/templates/**/*.html",
    "./backend/app/**/*.py"
  ],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Arial", "sans-serif"] },
      colors: {
        brand: { 50: "#eef4ff", 100: "#dbe7ff", 500: "#2563eb", 600: "#1d4ed8", 700: "#1e40af" },
        slate: { 25: "#f8fafc" },
        risk: { low: "#16a34a", medium: "#f59e0b", high: "#dc2626" }
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)",
      },
      borderRadius: { xl2: "1rem" }
    }
  },
  plugins: []
}
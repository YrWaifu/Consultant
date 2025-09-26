/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/app/templates/**/*.html",
    "./backend/app/**/*.py"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Arial", "sans-serif"]
      },
      colors: {
        brand: {
          50:  "#FFF3F2",
          100: "#FBE7E5",
          200: "#F5CFCC",
          300: "#EFA9A6",
          400: "#E37678",
          500: "#D84E5C", // основная кнопка
          600: "#C4314B", // бордовый ховер
          700: "#9F263B"  // тёмный бордовый
        },
        surface: {
          beige: "#F7F2EF" // бежевый фон страниц
        },
        risk: { low: "#16a34a", medium: "#f59e0b", high: "#dc2626" }
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)"
      },
      borderRadius: { xl2: "1rem" }
    }
  },
  plugins: []
}

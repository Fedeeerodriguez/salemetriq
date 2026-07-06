/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // SALEMETRIQ — "Pulse" aqua eléctrico sobre obsidiana, con champán de lujo.
        pulse: {
          50:  "#d7fdf5",
          100: "#a6f7e8",
          200: "#6ff0d6",
          300: "#3eecc9",
          400: "#23E7C4", // acento principal
          500: "#12cfac",
          600: "#0fa88f",
          700: "#0d8272",
          800: "#0b5f55",
          900: "#083f39",
        },
        champ: {
          DEFAULT: "#E3C79A", // metal de lujo / KPIs destacados
          deep:    "#B5945F",
        },
        surface: {
          DEFAULT: "#07090B", // obsidiana — fondo base
          card:    "#10171C", // paneles
          hover:   "#161F26",
          border:  "#24313A",
          muted:   "#1B252B",
        },
        // semánticos (separados del acento)
        up:   "#34E0A8",
        warn: "#E8B04B",
        down: "#F0736F",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'SFMono-Regular'", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

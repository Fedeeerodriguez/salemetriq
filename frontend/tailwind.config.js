/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // SALEMETRIQ — dashboard "Marcador": neutros casi-negros + acento ámbar/dorado.
        ink: {
          DEFAULT: "#0B0B0D", // fondo app
          card:    "#151417", // tarjetas
          raised:  "#1B1A1E", // cajas internas
          hover:   "#201F24",
          line:    "#26252A", // bordes
        },
        gold: {
          300: "#F6BC5E",
          400: "#F1AC43",
          500: "#E39A34", // acento principal
          600: "#C9862A",
        },
        pos: "#37D6A0", // positivo (verde-teal)
        neg: "#F0736F", // negativo (coral)
        txt: {
          DEFAULT: "#F4F4F3",
          soft:    "#9A9AA0",
          mute:    "#6E6E73",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'SFMono-Regular'", "Consolas", "monospace"],
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.1rem",
      },
    },
  },
  plugins: [],
};

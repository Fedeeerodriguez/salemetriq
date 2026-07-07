/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // SALEMETRIQ — UI espacial. Obsidiana + pulso violeta→cian (IA) + oro platino (premium).
        ink: {
          DEFAULT: "#0A0A0F", // obsidiana — fondo base (negro con tinte azul-violeta)
          card:    "#0F0F17", // tarjetas
          raised:  "#15151F", // cajas internas
          hover:   "#1C1C2A",
          line:    "#252536", // bordes fríos
        },
        // Violeta eléctrico → el inicio del gradiente-acento ("pulso" de la IA)
        iris: {
          400: "#8B5CF6",
          500: "#7C3AED", // acento principal
          600: "#6D28D9",
        },
        // Cian → el final del gradiente-acento
        cyan: {
          400: "#22D3EE",
          500: "#06B6D4",
        },
        // Oro platino → detalles de lujo, números destacados, KPIs premium
        gold: {
          300: "#E8C39E",
          400: "#D4AF7A",
          500: "#C79E68",
          600: "#B08A55",
        },
        pos: "#34D399", // positivo (verde menta)
        neg: "#FB7185", // negativo (coral/rosa)
        txt: {
          DEFAULT: "#F5F5F7", // blanco humo — texto principal
          soft:    "#A0A0B4", // gris frío — data secundaria
          mute:    "#6B6B80",
        },
      },
      fontFamily: {
        // display → Space Grotesk (títulos, KPIs); sans → Inter (cuerpo); mono → datos/telemetría
        display: ["'Space Grotesk'", "Inter", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'SFMono-Regular'", "Consolas", "monospace"],
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.1rem",
      },
      boxShadow: {
        glow:      "0 8px 30px -8px rgba(124,58,237,0.55)",
        "glow-cyan": "0 8px 30px -8px rgba(34,211,238,0.45)",
      },
      backgroundImage: {
        "accent-grad": "linear-gradient(120deg, #7C3AED 0%, #22D3EE 100%)",
      },
    },
  },
  plugins: [],
};

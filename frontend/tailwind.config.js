/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#121214", // Graphite near-black
        foreground: "#f8fafc", // Slate-50 off-white
        slate: {
          950: "#09090b",
          900: "#121214",
          800: "#1e1e24",
          700: "#2d2d34",
          400: "#94a3b8",
          300: "#cbd5e1"
        },
        amber: {
          500: "#d97706",
          600: "#b45309"
        },
        red: {
          500: "#ef4444"
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
        serif: ["IBM Plex Serif", "serif"]
      }
    },
  },
  plugins: [],
}

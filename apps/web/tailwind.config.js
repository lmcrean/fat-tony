/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'portfolio-bg': '#0a0a0a',
        'portfolio-card': '#1a1a1a',
        'portfolio-border': '#2a2a2a',
        'portfolio-text': '#e5e5e5',
        'portfolio-text-dim': '#999999',
        'portfolio-green': '#00d67e',
        'portfolio-red': '#ff5757',
      }
    },
  },
  plugins: [],
}

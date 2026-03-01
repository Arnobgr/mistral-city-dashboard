/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'french-blue': '#003189',
        'french-red': '#E1000F',
        'french-white': '#F8F8F8',
        'ink-black': '#0a0a0a',
      },
      fontFamily: {
        'display': ['"Bebas Neue"', 'sans-serif'],
        'body': ['"EB Garamond"', 'serif'],
        'mono': ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'brutal': '4px 4px 0px 0px rgba(0,49,137,1)',
        'brutal-hover': '8px 8px 0px 0px rgba(0,49,137,1)',
        'brutal-red': '4px 4px 0px 0px rgba(225,0,15,1)',
        'brutal-black': '4px 4px 0px 0px rgba(10,10,10,1)',
      }
    },
  },
  plugins: [],
}


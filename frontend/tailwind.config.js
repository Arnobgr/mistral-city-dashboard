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
      },
    },
  },
  plugins: [],
}


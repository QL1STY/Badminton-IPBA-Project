/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        jakarta: ['"Plus Jakarta Sans"', 'sans-serif'],
      },
      colors: {
        'brand-primary': '#ff6d00',
        'brand-secondary': '#dc2626',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
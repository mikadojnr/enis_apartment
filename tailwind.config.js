/** @type {import('tailwindcss').Config} */
module.exports = {
  // content: ["./src/**/*.{html,js}"],
  content: [
    "./app/templates/**/*.html",   // Flask HTML templates
    "./app/static/**/*.js",        // JS files (if any)
    "./app/static/**/*.css"       // CSS files (if any)
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}



// /** @type {import('tailwindcss').Config} */
// export default {
//   content: [
//     "./templates/**/*.html",   // Flask HTML templates
//     "./static/**/*.js",        // JS files (if any)
//     "./static/**/*.css"       // CSS files (if any)
//   ],,
//   theme: {
//     extend: {},
//   },
//   plugins: [],
// }

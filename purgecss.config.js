module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  css: [
    "./static/css/plugins.css",
    "./static/css/main_site.css",
  ],
  output: "./static/css/cleaned/",
  safelist: [
    "active",
    "show",
    "open",
  ],
};
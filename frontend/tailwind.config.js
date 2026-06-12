/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#1B2A4A",
        warm: "#F9F7F4",
        scarlet: "#CC0033",
        gold: "#E8A020",
        ink: "#233044",
        mist: "#E8EDF3",
      },
      boxShadow: {
        card: "0 16px 40px rgba(27, 42, 74, 0.08)",
      },
    },
  },
  plugins: [],
};

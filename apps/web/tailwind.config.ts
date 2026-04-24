import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f5f7f9",
        panel: "#ffffff",
        shell: "#eef2f5",
        ink: "#191c1e",
        muted: "#697178",
        steel: "#3e5c76",
        steelDeep: "#26445d",
        steelSoft: "#d7e4ec",
        sand: "#c6b59a",
        line: "#d9dde1",
        riskLow: "#f6d9bf",
        riskMedium: "#f0c59f",
        riskHigh: "#d99293",
      },
      boxShadow: {
        panel: "0 16px 40px rgba(25, 28, 30, 0.06)",
        inset: "inset 0 1px 0 rgba(255,255,255,0.7)",
      },
      backgroundImage: {
        "header-grid":
          "linear-gradient(rgba(62, 92, 118, 0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(62, 92, 118, 0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;

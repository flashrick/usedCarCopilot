import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        primary: "#2563EB",
        primaryDeep: "#1D4ED8",
        primarySoft: "#DBEAFE",
        secondary: "#06B6D4",
        secondaryDeep: "#0E7490",
        secondarySoft: "#CFFAFE",
        accent: "#F97316",
        accentDeep: "#EA580C",
        accentSoft: "#FFEDD5",
        textStrong: "#111827",
        textBody: "#374151",
        textMuted: "#6B7280",
        borderLight: "#E5E7EB",
        panel: "#ffffff",
        shell: "#F1F5F9",
        shellDeep: "#E2E8F0",
        canvas: "#F8FAFC",
        ink: "#111827",
        muted: "#374151",
        mutedSoft: "#6B7280",
        steel: "#2563EB",
        steelDeep: "#1D4ED8",
        steelSoft: "#DBEAFE",
        sand: "#FFEDD5",
        line: "#E5E7EB",
        riskLow: "#DCFCE7",
        riskMedium: "#FEF3C7",
        riskHigh: "#FEE2E2",
        riskLowInk: "#166534",
        riskMediumInk: "#9A3412",
        riskHighInk: "#991B1B",
        success: "#16A34A",
        successSoft: "#DCFCE7",
      },
      boxShadow: {
        panel: "0 20px 48px rgba(15, 23, 42, 0.08)",
        soft: "0 10px 24px rgba(37, 99, 235, 0.08)",
        inset: "inset 0 1px 0 rgba(255,255,255,0.72)",
      },
      backgroundImage: {
        "header-grid":
          "linear-gradient(rgba(37, 99, 235, 0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(6, 182, 212, 0.06) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;

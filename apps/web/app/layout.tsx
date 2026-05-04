import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { LanguageToggle } from "@/components/i18n/language-toggle";
import { LocaleProvider } from "@/components/i18n/locale-provider";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-plex-sans",
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-plex-mono",
  weight: ["400", "500"],
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Used Car Copilot | 二手车 Copilot",
  description: "AI-backed used-car search with English and Simplified Chinese interface support.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable} ${spaceGrotesk.variable}`}>
      <body className="font-[var(--font-plex-sans)]">
        <LocaleProvider>
          <LanguageToggle />
          {children}
        </LocaleProvider>
      </body>
    </html>
  );
}

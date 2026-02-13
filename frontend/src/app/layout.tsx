import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "VPN Monitor",
  description: "Мониторинг VPN-профилей для России",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect rx='20' width='100' height='100' fill='%237c3aed'/><text x='50' y='72' text-anchor='middle' fill='white' font-size='60' font-family='sans-serif' font-weight='bold'>V</text></svg>",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}

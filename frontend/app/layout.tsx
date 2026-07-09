import "./globals.css";
import type { Metadata } from "next";
import { plexMono, plexSans } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "AI Quant Signal Platform",
  description: "Quant research showcase for portfolio and research demonstration.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${plexSans.variable} ${plexMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}

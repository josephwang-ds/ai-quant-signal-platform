import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Quant Signal Platform",
  description: "Quant research showcase for portfolio and research demonstration.",
};

// 根布局：应用全局样式与页面结构
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

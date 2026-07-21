import "./globals.css";
import { plexMono, plexSans } from "@/lib/fonts";
import { rootMetadata } from "@/lib/productIdentity";

export const metadata = rootMetadata;

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

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "CJPHub — Internet Culture Observatory",
  description: "Independent real-time observatory tracking narratives, memes, and platform events for internet-native movements.",
  openGraph: {
    title: "CJPHub — Internet Culture Observatory",
    description: "Independent real-time observatory tracking narratives, memes, and platform events for internet-native movements.",
    type: "website",
    url: "https://cjphub.com"
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="antialiased min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}

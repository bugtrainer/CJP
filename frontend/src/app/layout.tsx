// layout.tsx — CJPHub Root Layout with Upgraded SEO Metadata

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

// ─── SEO Metadata ──────────────────────────────────────────────────────────────

export const metadata: Metadata = {
  // ── Core ────────────────────────────────────────────────────────────────────
  metadataBase: new URL("https://www.cjphub.com"),
  title: {
    default: "CJPHub — Internet Culture Observatory",
    template: "%s | CJPHub Observatory",
  },
  description:
    "Independent real-time observatory tracking narratives, memes, and platform events for internet-native movements. Live telemetry, narrative graphs, and verified milestones.",
  keywords: [
    "cjphub",
    "internet culture",
    "meme tracking",
    "social media analytics",
    "narrative observatory",
    "Cockroach Janta Party",
    "CJP movement",
    "India protest memes",
    "digital discourse analysis",
    "viral movement tracker",
    "platform censorship monitor",
    "real-time social signals",
    "student protest India",
    "Gen Z political satire",
    "online narrative graph",
    "memetic research",
  ],
  authors: [{ name: "CJPHub Observatory" }],
  creator: "CJPHub",
  publisher: "CJPHub",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://www.cjphub.com/",
  },

  // ── Open Graph ───────────────────────────────────────────────────────────────
  openGraph: {
    type: "website",
    locale: "en_IN",
    url: "https://www.cjphub.com/",
    siteName: "CJPHub — Internet Culture Observatory",
    title: "CJPHub — Internet Culture Observatory",
    description:
      "Real-time observatory tracking narratives, memes, and platform interventions for internet-native movements. Live narrative graphs and verified milestones.",
    images: [
      {
        url: "/og-image.png",   // place a 1200×630 image at /public/og-image.png
        width: 1200,
        height: 630,
        alt: "CJPHub — Internet Culture Observatory",
      },
    ],
  },

  // ── Twitter / X Card ────────────────────────────────────────────────────────
  twitter: {
    card: "summary_large_image",
    site: "@cjphub",          // update when you have a handle
    creator: "@cjphub",
    title: "CJPHub — Internet Culture Observatory",
    description:
      "Live telemetry on internet movements — narrative graphs, censorship logs, and real-time meme tracking.",
    images: ["/og-image.png"],
  },

  // ── Icons ────────────────────────────────────────────────────────────────────
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/apple-touch-icon.png",
  },

  // ── Manifest ────────────────────────────────────────────────────────────────
  manifest: "/site.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#0b0f0e",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

// ─── Layout ───────────────────────────────────────────────────────────────────

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* Structured Data — WebSite schema */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: "CJPHub — Internet Culture Observatory",
              url: "https://www.cjphub.com",
              description:
                "Independent real-time observatory tracking narratives, memes, and platform events for internet-native movements.",
              potentialAction: {
                "@type": "SearchAction",
                target: {
                  "@type": "EntryPoint",
                  urlTemplate: "https://www.cjphub.com/?q={search_term_string}",
                },
                "query-input": "required name=search_term_string",
              },
            }),
          }}
        />
      </head>
      <body className={`${inter.className} antialiased min-h-screen bg-[#070b09] text-slate-100`}>
        {children}
      </body>
    </html>
  );
}

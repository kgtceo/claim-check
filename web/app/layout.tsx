import type { Metadata } from "next";
import "./globals.css";

const url = "https://claimcheck.kareemghazal.com";
const title = "claim-check — patent claim structure & antecedent-basis linter";
const description =
  "Paste a numbered patent claim set and get a heuristic structural review: claim dependencies, antecedent-basis gaps, single-sentence and indefiniteness checks. Educational — not legal advice.";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url,
    siteName: "claim-check",
    title,
    description,
    locale: "en_GB",
    images: [{ url: "/og.jpg", width: 1200, height: 630, alt: "claim-check — patent claim structure & antecedent-basis linter" }],
  },
  twitter: { card: "summary_large_image", title, description, images: ["/og.jpg"] },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

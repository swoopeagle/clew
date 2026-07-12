import type { Metadata } from "next";
import { Fraunces, Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"] });
const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["600", "700"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "Clew — Grant Board",
  description:
    "Live view of your grant pipeline: every prospect Clew found, screened, and tracked — sourced, never fabricated.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geist.className} ${fraunces.variable}`}>
        {children}
      </body>
    </html>
  );
}

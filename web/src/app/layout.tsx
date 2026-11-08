import type { Metadata, Viewport } from "next";
import { Archivo } from "next/font/google";

import { Footer } from "@/components/Footer";
import { Masthead } from "@/components/Masthead";
import { AuthProvider } from "@/lib/auth";

import "./globals.css";

const archivo = Archivo({
  subsets: ["latin"],
  axes: ["wdth"],
  variable: "--font-archivo",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AcademixAI: what changed in AI research today",
    template: "%s · AcademixAI",
  },
  description:
    "A daily map of the AI papers that changed the field, with every paper explained at your level: Plain, Student or Expert.",
};

export const viewport: Viewport = {
  themeColor: "#16171a",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={archivo.variable}>
      <body className="flex min-h-dvh flex-col">
        <AuthProvider>
          <Masthead />
          <main id="main" className="flex-1">
            {children}
          </main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}

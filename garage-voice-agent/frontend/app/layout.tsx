import type { Metadata } from "next";
import Link from "next/link";

import "../styles/globals.css";

export const metadata: Metadata = {
  title: "VoiceAuto",
  description: "Démo d'assistant téléphonique IA pour garages.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr">
      <body>
        <header className="border-b border-border bg-white/85 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center px-6 py-4">
            <Link href="/" className="text-xl font-semibold tracking-tight text-ink">
              <span>VoiceAuto</span>
            </Link>
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

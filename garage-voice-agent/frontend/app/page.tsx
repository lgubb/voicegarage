import Link from "next/link";

import { Button } from "@/components/ui/Button";

const heroDescription =
  "VoiceAuto accompagne les appels, comprend la demande du client, prend les rendez-vous et les ajoute au calendrier, tout en préparant les informations utiles pour que votre équipe garde le contrôle.";

export default function HomePage() {
  return (
    <div className="mx-auto flex min-h-[calc(100vh-80px)] max-w-6xl items-center justify-center px-6 py-16">
      <section className="home-fade-in mx-auto max-w-4xl text-center">
        <p className="home-brand-write mb-5 text-3xl font-semibold tracking-tight sm:text-4xl">
          VoiceAuto
        </p>
        <h1 className="mx-auto max-w-4xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl">
          Un accueil téléphonique plus fluide pour votre garage ou carrosserie
        </h1>
        <p className="home-copy-animate mx-auto mt-6 max-w-2xl text-lg font-medium leading-8">
          {heroDescription}
        </p>
        <div className="mt-9 flex justify-center">
          <Link href="/demo">
            <Button className="h-12 px-6 text-base shadow-soft">
              Tester la démo
            </Button>
          </Link>
        </div>
        <div className="home-wave mx-auto mt-10 flex h-16 w-full max-w-md items-center justify-center gap-2">
          {[1, 2, 3, 4, 5, 6, 7].map((bar) => (
            <span key={bar} className="home-wave-bar rounded-full bg-accent" />
          ))}
        </div>
      </section>
    </div>
  );
}

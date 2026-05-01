"use client";

import { useEffect, useRef, useState } from "react";
import { CalendarCheck, Car, ClipboardCheck, Mic, MicOff, Phone, PhoneOff, RotateCcw, UserRound } from "lucide-react";
import { RoomEvent, type Room } from "livekit-client";

import { createSession } from "@/lib/api";
import { connectToLiveKit, requestCallSheetFinalization, type VoiceAutoCallSheetPayload } from "@/lib/livekit";
import type { Scenario, SessionCreateResponse, Voice } from "@/lib/types";
import { Button } from "./ui/Button";
import { Badge } from "./ui/Badge";
import { Panel } from "./ui/Panel";
import { ScenarioSelector } from "./ScenarioSelector";

type ConnectionState = "disconnected" | "creating" | "connecting" | "connected" | "finalizing" | "error";
type TutorialStep = "create" | "connect" | "disconnect";
type DemoCallSheet = {
  client: string;
  phone: string;
  vehicle: string;
  request: string;
  appointment: string;
  calendar: string;
  note: string;
  appointmentConfirmed: boolean;
  appointmentReceived: boolean;
  recordReceived: boolean;
};

function TutorialCallout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <div className="mr-2 flex shrink-0 items-center lg:hidden">
        <div className="flex items-center gap-2 whitespace-nowrap rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-950 shadow-sm">
          <span className="h-2.5 w-2.5 rounded-full bg-accent" />
          {children}
        </div>
        <span className="h-px w-4 bg-accent" />
        <span className="h-3 w-3 rounded-full border-2 border-accent bg-white" />
      </div>
      <div className="pointer-events-none absolute right-[calc(100%+14px)] top-1/2 z-10 hidden -translate-y-1/2 items-center lg:flex">
        <div className="whitespace-nowrap rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-950 shadow-sm">
          {children}
        </div>
        <span className="h-px w-7 bg-accent" />
        <span className="h-3 w-3 rounded-full border-2 border-accent bg-white" />
      </div>
    </>
  );
}

function asObject(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
}

function textValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function fallbackValue(value: string | null | undefined, fallback: string): string {
  return value && value.trim() ? value.trim() : fallback;
}

function formatVehicle(value: unknown): string | null {
  const vehicle = asObject(value);
  if (!vehicle) return null;
  const parts = [vehicle.make, vehicle.model, vehicle.license_plate].map(textValue).filter(Boolean);
  return parts.length ? parts.join(" ") : null;
}

function formatDateTime(value: unknown): string | null {
  const rawValue = textValue(value);
  if (!rawValue) return null;

  const isoWallClock = rawValue.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (isoWallClock) {
    const [, year, month, day, hour, minute] = isoWallClock;
    const wallDate = new Date(Number(year), Number(month) - 1, Number(day));
    const datePart = new Intl.DateTimeFormat("fr-FR", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }).format(wallDate);

    return `${datePart.charAt(0).toUpperCase()}${datePart.slice(1)} à ${Number(hour)} h ${minute}`;
  }

  const date = new Date(rawValue);
  if (Number.isNaN(date.getTime())) {
    return rawValue;
  }

  const datePart = new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(date);
  const timePart = new Intl.DateTimeFormat("fr-FR", {
    hour: "numeric",
    minute: "2-digit",
  })
    .format(date)
    .replace(":", " h ");

  return `${datePart.charAt(0).toUpperCase()}${datePart.slice(1)} à ${timePart}`;
}

function serviceLabel(value: unknown): string | null {
  const service = textValue(value);
  if (!service) return null;
  const labels: Record<string, string> = {
    revision: "Révision",
    revision_entretien: "Révision et entretien",
    pneus: "Pneus",
    carrosserie: "Carrosserie",
    panne: "Panne",
    diagnostic: "Diagnostic",
    devis: "Devis",
    urgence: "Panne urgente",
    autre: "Demande personnalisée",
  };
  return labels[service] ?? service.replaceAll("_", " ");
}

function noteFromRecord(record: Record<string, unknown>): string | null {
  const risks = Array.isArray(record.risk_flags)
    ? record.risk_flags.map(textValue).filter(Boolean)
    : [];
  if (risks.length) {
    return risks.join(". ");
  }
  return null;
}

function mergeCallSheetPayload(current: DemoCallSheet | null, payload: VoiceAutoCallSheetPayload): DemoCallSheet | null {
  const appointment = asObject(payload.appointment);
  const record = asObject(payload.record);

  if (!appointment && !record) {
    return current;
  }

  const caller = asObject(record?.caller);
  const appointmentVehicle = appointment ? formatVehicle(appointment.vehicle) : null;
  const recordVehicle = record ? formatVehicle(record.vehicle) : null;
  const appointmentService = appointment ? serviceLabel(appointment.service_type) : null;
  const recordSummary = textValue(record?.summary);
  const appointmentNotes = textValue(appointment?.notes);
  const requestedAction = serviceLabel(record?.intent);
  const appointmentDate = appointment ? formatDateTime(appointment.datetime) : null;
  const appointmentConfirmed = current?.appointmentConfirmed ?? false;
  const appointmentReceived = current?.appointmentReceived ?? false;
  const recordReceived = current?.recordReceived ?? false;

  return {
    client: fallbackValue(
      textValue(appointment?.caller_name) ?? textValue(caller?.name) ?? current?.client,
      "Client non renseigné",
    ),
    phone: fallbackValue(textValue(appointment?.phone) ?? textValue(caller?.phone) ?? current?.phone, "Non renseigné"),
    vehicle: fallbackValue(appointmentVehicle ?? recordVehicle ?? current?.vehicle, "Véhicule non renseigné"),
    request: fallbackValue(
      recordSummary ?? appointmentNotes ?? appointmentService ?? requestedAction ?? current?.request,
      "Demande notée pendant l'appel.",
    ),
    appointment: fallbackValue(appointmentDate ?? current?.appointment, "À confirmer avec le client"),
    calendar: appointment
      ? "Créneau ajouté au calendrier du garage."
      : (current?.calendar ?? "Aucun créneau confirmé pour le moment."),
    note: fallbackValue(
      appointmentNotes ?? noteFromRecord(record ?? {}) ?? current?.note,
      "Informations collectées pendant l'appel.",
    ),
    appointmentConfirmed: appointment ? true : appointmentConfirmed,
    appointmentReceived: appointment ? true : appointmentReceived,
    recordReceived: record ? true : recordReceived,
  };
}

function DemoCallSheetPanel({ sheet }: Readonly<{ sheet: DemoCallSheet }>) {
  const rows = [
    { icon: UserRound, label: "Client", value: sheet.client },
    { icon: Phone, label: "Téléphone", value: sheet.phone },
    { icon: Car, label: "Véhicule", value: sheet.vehicle },
    { icon: ClipboardCheck, label: "Demande", value: sheet.request },
    { icon: CalendarCheck, label: "Rendez-vous", value: sheet.appointment },
  ];

  return (
    <Panel className="call-sheet-reveal mt-5 overflow-hidden shadow-soft">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-accent">Fiche générée</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">Résumé pour le garage</h2>
        </div>
        <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-semibold text-blue-950">
          {sheet.appointmentConfirmed ? "Rendez-vous confirmé" : "Fiche prête"}
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((row) => {
          const Icon = row.icon;
          return (
            <div key={row.label} className="rounded-lg border border-border bg-surface p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium text-muted">
                <Icon size={16} className="text-accent" />
                {row.label}
              </div>
              <p className="text-base font-semibold text-ink">{row.value}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-900">Calendrier</p>
          <p className="mt-2 text-base font-semibold text-blue-950">{sheet.calendar}</p>
        </div>
        <div className="rounded-lg border border-border bg-white p-4">
          <p className="text-sm font-medium text-muted">À retenir</p>
          <p className="mt-2 text-base font-semibold text-ink">{sheet.note}</p>
        </div>
      </div>
    </Panel>
  );
}

export function VoiceDemoPanel() {
  const [scenario, setScenario] = useState<Scenario>("revision");
  const [voice, setVoice] = useState<Voice>("femme");
  const [session, setSession] = useState<SessionCreateResponse | null>(null);
  const [room, setRoom] = useState<Room | null>(null);
  const [muted, setMuted] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [error, setError] = useState<string | null>(null);
  const [callSheet, setCallSheet] = useState<DemoCallSheet | null>(null);
  const pendingCallSheetRef = useRef<DemoCallSheet | null>(null);
  const finalizeResolverRef = useRef<(() => void) | null>(null);
  const tutorialStep: TutorialStep =
    connectionState === "connected" || connectionState === "finalizing" ? "disconnect" : session ? "connect" : "create";

  function handleCallSheetUpdate(payload: VoiceAutoCallSheetPayload) {
    const nextSheet = mergeCallSheetPayload(pendingCallSheetRef.current, payload);
    pendingCallSheetRef.current = nextSheet;
    if (nextSheet?.recordReceived) {
      setCallSheet(nextSheet);
      setError(null);
    }
    finalizeResolverRef.current?.();
    finalizeResolverRef.current = null;
  }

  function waitForCallSheet(timeoutMs: number): Promise<void> {
    if (pendingCallSheetRef.current?.recordReceived) {
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      const timeout = window.setTimeout(() => {
        if (finalizeResolverRef.current === finish) {
          finalizeResolverRef.current = null;
        }
        resolve();
      }, timeoutMs);

      function finish() {
        window.clearTimeout(timeout);
        resolve();
      }

      finalizeResolverRef.current = finish;
    });
  }

  useEffect(() => {
    if (!room) return;

    function handleRoomDisconnected() {
      setRoom(null);
      setConnectionState("disconnected");
      if (pendingCallSheetRef.current?.recordReceived) {
        setCallSheet(pendingCallSheetRef.current);
      }
    }

    room.on(RoomEvent.Disconnected, handleRoomDisconnected);
    return () => {
      room.off(RoomEvent.Disconnected, handleRoomDisconnected);
    };
  }, [room]);

  async function handleCreateSession() {
    setError(null);
    setCallSheet(null);
    pendingCallSheetRef.current = null;
    setConnectionState("creating");
    try {
      const nextSession = await createSession({ garage_id: "demo-garage", scenario, voice });
      setSession(nextSession);
      setConnectionState("disconnected");
    } catch (sessionError) {
      setConnectionState("error");
      setError(sessionError instanceof Error ? sessionError.message : "Erreur création session");
    }
  }

  async function handleConnect() {
    if (!session) return;
    setError(null);
    setConnectionState("connecting");
    try {
      const connection = await connectToLiveKit(session, { onCallSheet: handleCallSheetUpdate });
      setRoom(connection.room);
      setMuted(false);
      setConnectionState("connected");
    } catch (connectError) {
      setConnectionState("error");
      setError(connectError instanceof Error ? connectError.message : "Erreur de connexion");
    }
  }

  async function handleMuteToggle() {
    if (!room) return;
    const nextMuted = !muted;
    await room.localParticipant.setMicrophoneEnabled(!nextMuted);
    setMuted(nextMuted);
  }

  async function handleDisconnect() {
    if (!room) return;

    if (pendingCallSheetRef.current?.recordReceived) {
      setCallSheet(pendingCallSheetRef.current);
      room.disconnect();
      setRoom(null);
      setConnectionState("disconnected");
      return;
    }

    setError(null);
    setConnectionState("finalizing");
    try {
      await requestCallSheetFinalization(room);
      await waitForCallSheet(10000);
    } catch (finalizeError) {
      console.warn("[livekit] call sheet finalization request failed", finalizeError);
    }

    if (pendingCallSheetRef.current?.recordReceived) {
      setCallSheet(pendingCallSheetRef.current);
    } else {
      setError("La fiche n'a pas encore été reçue. Relancez une session et confirmez le créneau avec l'agent.");
    }

    room.disconnect();
    setRoom(null);
    setConnectionState("disconnected");
  }

  return (
    <div>
      <Panel className="shadow-soft">
        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-ink">
                Tester l'assistant téléphonique{" "}
                <span className="home-brand-write">VoiceAuto</span>
              </h1>
            </div>
            <ScenarioSelector value={scenario} onChange={setScenario} />
          </div>

          <div className="relative overflow-visible rounded-lg border border-border bg-surface p-4">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm font-medium text-ink">Voix</span>
              <div className="flex rounded-md border border-border bg-white p-1">
                {(["femme", "homme"] as Voice[]).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setVoice(item)}
                    className={`rounded px-3 py-1.5 text-sm ${voice === item ? "bg-ink text-white" : "text-muted"}`}
                  >
                    {item === "femme" ? "Femme" : "Homme"}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-4 flex items-center justify-between rounded-md border border-border bg-white p-3">
              <span className="text-sm text-muted">État</span>
              <Badge tone={connectionState === "connected" ? "green" : connectionState === "error" ? "red" : "default"}>
                {connectionState}
              </Badge>
            </div>

            <div className="mb-4 flex h-14 items-center justify-center gap-1 rounded-md bg-white">
              {[1, 2, 3, 4].map((item) => (
                <span
                  key={item}
                  className={`audio-bar w-2 rounded-full ${connectionState === "connected" ? "bg-accent" : "bg-slate-300"}`}
                />
              ))}
            </div>

            <div className="grid gap-2">
              <div className="relative flex items-center">
                {tutorialStep === "create" ? <TutorialCallout>Cliquez ici</TutorialCallout> : null}
                <Button
                  onClick={handleCreateSession}
                  disabled={connectionState === "creating"}
                  className={tutorialStep === "create" ? "flex-1 ring-2 ring-accent ring-offset-2" : "w-full"}
                >
                  <RotateCcw size={16} />
                  Créer une session
                </Button>
              </div>
              <div className="relative flex items-center">
                {tutorialStep === "connect" ? <TutorialCallout>Cliquez ici</TutorialCallout> : null}
                <Button
                  variant="secondary"
                  onClick={handleConnect}
                  disabled={!session || connectionState === "connecting" || connectionState === "connected"}
                  className={tutorialStep === "connect" ? "flex-1 ring-2 ring-accent ring-offset-2" : "w-full"}
                >
                  <Phone size={16} />
                  Se connecter à l'agent
                </Button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <Button variant="secondary" onClick={handleMuteToggle} disabled={!room}>
                  {muted ? <MicOff size={16} /> : <Mic size={16} />}
                  {muted ? "Unmute" : "Mute"}
                </Button>
                <div className="relative flex items-center">
                  {tutorialStep === "disconnect" ? <TutorialCallout>Terminez ici</TutorialCallout> : null}
                  <Button
                    variant="secondary"
                    onClick={handleDisconnect}
                    disabled={!room || connectionState === "finalizing"}
                    className={tutorialStep === "disconnect" ? "flex-1 ring-2 ring-accent ring-offset-2" : "w-full"}
                  >
                    <PhoneOff size={16} />
                    {connectionState === "finalizing" ? "Préparation..." : "Disconnect"}
                  </Button>
                </div>
              </div>
            </div>

            {error ? <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          </div>
        </div>
      </Panel>
      {callSheet ? <DemoCallSheetPanel sheet={callSheet} /> : null}
    </div>
  );
}

import { Room, RoomEvent, Track, type RemoteParticipant, type RemoteTrack } from "livekit-client";

import type { SessionCreateResponse } from "./types";

export type LiveKitConnection = {
  room: Room;
};

export type VoiceAutoCallSheetPayload = {
  type: "voiceauto_call_sheet";
  source?: "appointment" | "record";
  appointment?: unknown;
  record?: unknown;
};

type LiveKitConnectionOptions = {
  onCallSheet?: (payload: VoiceAutoCallSheetPayload) => void;
};

export async function requestCallSheetFinalization(room: Room): Promise<void> {
  const payload = new TextEncoder().encode(JSON.stringify({ type: "voiceauto_finalize" }));
  await room.localParticipant.publishData(payload, {
    reliable: true,
    topic: "voiceauto_finalize",
  });
}

function logLiveKit(message: string, details?: Record<string, unknown>): void {
  console.info(`[livekit] ${message}`, details ?? {});
}

function warnLiveKit(message: string, error: unknown): void {
  console.warn(`[livekit] ${message}`, error);
}

async function startRoomAudio(room: Room, reason: string): Promise<void> {
  try {
    await room.startAudio();
    logLiveKit("audio playback started", { reason, canPlaybackAudio: room.canPlaybackAudio });
  } catch (error) {
    warnLiveKit(`audio playback blocked (${reason})`, error);
  }
}

function removeRemoteAudioElements(): void {
  document.querySelectorAll("[data-livekit-remote-audio='true']").forEach((element) => element.remove());
}

function findMountedAudio(trackSid: string): HTMLMediaElement | null {
  const elements = document.querySelectorAll<HTMLMediaElement>("[data-livekit-track-sid]");
  return Array.from(elements).find((element) => element.dataset.livekitTrackSid === trackSid) ?? null;
}

function remoteAudioId(track: RemoteTrack): string {
  return track.sid ?? track.mediaStreamTrack.id;
}

function mountRemoteAudio(track: RemoteTrack, participant?: RemoteParticipant): HTMLMediaElement | null {
  if (track.kind !== Track.Kind.Audio) {
    return null;
  }

  const trackId = remoteAudioId(track);
  if (findMountedAudio(trackId)) {
    return null;
  }

  const element = track.attach();
  element.autoplay = true;
  element.controls = false;
  element.muted = false;
  element.dataset.livekitRemoteAudio = "true";
  element.dataset.livekitTrackSid = trackId;
  element.style.position = "absolute";
  element.style.width = "1px";
  element.style.height = "1px";
  element.style.opacity = "0";
  element.style.pointerEvents = "none";
  document.body.appendChild(element);

  logLiveKit("remote audio track attached", {
    participant: participant?.identity,
    trackSid: track.sid,
    trackId,
  });

  void element.play().catch((error) => {
    warnLiveKit("remote audio element play failed", error);
  });

  return element;
}

function unmountRemoteAudio(track: RemoteTrack): void {
  track.detach().forEach((element) => element.remove());
}

function mountExistingRemoteAudio(room: Room): void {
  room.remoteParticipants.forEach((participant) => {
    participant.audioTrackPublications.forEach((publication) => {
      if (publication.track) {
        mountRemoteAudio(publication.track, participant);
      }
    });
  });
}

function decodeDataPayload(payload: Uint8Array): unknown {
  try {
    return JSON.parse(new TextDecoder().decode(payload));
  } catch (error) {
    warnLiveKit("data payload decode failed", error);
    return null;
  }
}

function isCallSheetPayload(payload: unknown): payload is VoiceAutoCallSheetPayload {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "type" in payload &&
    payload.type === "voiceauto_call_sheet"
  );
}

export async function connectToLiveKit(
  session: SessionCreateResponse,
  options: LiveKitConnectionOptions = {},
): Promise<LiveKitConnection> {
  const room = new Room({
    adaptiveStream: true,
    dynacast: true,
  });

  room.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
    mountRemoteAudio(track, participant);
    void startRoomAudio(room, "track_subscribed");
  });

  room.on(RoomEvent.TrackUnsubscribed, (track) => {
    unmountRemoteAudio(track);
  });

  room.on(RoomEvent.TrackSubscriptionFailed, (trackSid, participant, error) => {
    warnLiveKit("track subscription failed", {
      error,
      participant: participant.identity,
      trackSid,
    });
  });

  room.on(RoomEvent.AudioPlaybackStatusChanged, () => {
    logLiveKit("audio playback status changed", { canPlaybackAudio: room.canPlaybackAudio });
    if (!room.canPlaybackAudio) {
      void startRoomAudio(room, "audio_playback_status_changed");
    }
  });

  room.on(RoomEvent.ConnectionStateChanged, (state) => {
    logLiveKit("connection state changed", { state });
  });

  room.on(RoomEvent.DataReceived, (payload, participant, _kind, topic) => {
    const decodedPayload = decodeDataPayload(payload);
    if (isCallSheetPayload(decodedPayload)) {
      options.onCallSheet?.(decodedPayload);
      logLiveKit("call sheet update received", { participant: participant?.identity, topic });
    }
  });

  room.on(RoomEvent.MediaDevicesError, (error) => {
    warnLiveKit("media devices error", error);
  });

  room.on(RoomEvent.Disconnected, (reason) => {
    logLiveKit("disconnected", { reason });
    removeRemoteAudioElements();
  });

  await startRoomAudio(room, "before_connect");
  await room.connect(session.livekit_url, session.token);
  mountExistingRemoteAudio(room);
  await startRoomAudio(room, "after_connect");
  await room.localParticipant.setMicrophoneEnabled(true);
  await startRoomAudio(room, "after_microphone_enabled");
  return { room };
}

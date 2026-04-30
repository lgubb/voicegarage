export type Scenario = "revision" | "pneus" | "carrosserie" | "panne_urgente" | "custom";
export type Voice = "femme" | "homme";

export type SessionCreateResponse = {
  room_name: string;
  participant_identity: string;
  livekit_url: string;
  token: string;
  call_id: string;
};

export type TranscriptMessage = {
  role: string;
  text: string;
};

export type ToolCall = {
  name: string;
  arguments?: Record<string, unknown>;
  status?: string;
  elapsed_ms?: number;
};

export type StructuredSummary = {
  caller_name: string | null;
  phone: string | null;
  email: string | null;
  vehicle_make: string | null;
  vehicle_model: string | null;
  license_plate: string | null;
  intent: string;
  urgency: "low" | "medium" | "high";
  requested_action: string;
  appointment_status: string;
  appointment_datetime: string | null;
  summary_for_garage: string;
  missing_info: string[];
  risk_flags: string[];
  tool_calls: string[];
  next_action: string;
};

export type Appointment = {
  appointment_id: string;
  caller_name: string | null;
  phone: string | null;
  vehicle: {
    make: string | null;
    model: string | null;
    license_plate: string | null;
  };
  service_type: string;
  datetime: string;
  status: string;
  notes: string | null;
};

export type CallRecord = {
  id: string;
  garage_id: string;
  scenario: string;
  metadata: Record<string, unknown>;
  transcript: TranscriptMessage[];
  tool_calls: ToolCall[];
  structured_summary: StructuredSummary | null;
  appointment: Appointment | null;
  status: string;
  timestamps: {
    created_at: string;
    updated_at: string;
  };
};

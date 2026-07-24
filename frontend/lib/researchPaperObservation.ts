export type PaperObservationCadence = "daily" | "weekly" | "monthly";
export type PaperObservationStatus = "active" | "completed";

export type PaperObservationEntry = {
  id: string;
  observedAt: string;
  note: string;
};

export type PaperObservationSession = {
  researchId: string;
  status: PaperObservationStatus;
  cadence: PaperObservationCadence;
  minimumDays: number;
  exitCriteria: string;
  startedAt: string;
  completedAt: string | null;
  entries: PaperObservationEntry[];
};

export const PAPER_OBSERVATION_STORAGE_KEY =
  "quant.research.paper-observation.v1";

type SessionMap = Record<string, PaperObservationSession>;

function readAll(): SessionMap {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(PAPER_OBSERVATION_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as SessionMap) : {};
  } catch {
    return {};
  }
}

function writeAll(sessions: SessionMap): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(
    PAPER_OBSERVATION_STORAGE_KEY,
    JSON.stringify(sessions)
  );
}

export function getPaperObservationSession(
  researchId: string
): PaperObservationSession | null {
  return readAll()[researchId] ?? null;
}

export function startPaperObservationSession(input: {
  researchId: string;
  cadence: PaperObservationCadence;
  minimumDays: number;
  exitCriteria: string;
  now?: string;
}): PaperObservationSession {
  const minimumDays = Math.max(1, Math.round(input.minimumDays));
  const exitCriteria = input.exitCriteria.trim();
  if (!exitCriteria) throw new Error("Exit criteria are required.");
  const session: PaperObservationSession = {
    researchId: input.researchId,
    status: "active",
    cadence: input.cadence,
    minimumDays,
    exitCriteria,
    startedAt: input.now ?? new Date().toISOString(),
    completedAt: null,
    entries: [],
  };
  writeAll({ ...readAll(), [input.researchId]: session });
  return session;
}

export function addPaperObservationEntry(input: {
  researchId: string;
  note: string;
  now?: string;
}): PaperObservationSession {
  const sessions = readAll();
  const session = sessions[input.researchId];
  if (!session || session.status !== "active") {
    throw new Error("An active observation session is required.");
  }
  const note = input.note.trim();
  if (!note) throw new Error("Observation note is required.");
  const observedAt = input.now ?? new Date().toISOString();
  const updated: PaperObservationSession = {
    ...session,
    entries: [
      ...session.entries,
      {
        id: `observation-${Date.parse(observedAt)}-${session.entries.length}`,
        observedAt,
        note,
      },
    ],
  };
  writeAll({ ...sessions, [input.researchId]: updated });
  return updated;
}

export function completePaperObservationSession(
  researchId: string,
  now?: string
): PaperObservationSession {
  const sessions = readAll();
  const session = sessions[researchId];
  if (!session) throw new Error("Observation session not found.");
  const updated: PaperObservationSession = {
    ...session,
    status: "completed",
    completedAt: now ?? new Date().toISOString(),
  };
  writeAll({ ...sessions, [researchId]: updated });
  return updated;
}

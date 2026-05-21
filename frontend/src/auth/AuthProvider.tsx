import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { AuthContextValue, AuthSession } from "./types";

const AUTH_SESSION_KEY = "job-alert.auth-session.v1";
const MOCK_GOOGLE_USER = {
  id: "mock-google-session",
  displayName: "Mock Google User",
  provider: "mock-google",
} as const;

const anonymousSession: AuthSession = {
  mode: "mock",
  status: "anonymous",
  user: null,
  onboarding: {
    status: "not_started",
    step: 0,
  },
};

const AuthContext = createContext<AuthContextValue | null>(null);

function clampOnboardingStep(step: number): number {
  return Math.max(0, Math.min(4, step));
}

function readSession(): AuthSession {
  const stored = window.sessionStorage.getItem(AUTH_SESSION_KEY);
  if (!stored) return anonymousSession;

  try {
    const parsed = JSON.parse(stored) as Partial<AuthSession>;
    if (parsed.mode !== "mock" || parsed.status !== "authenticated" || parsed.user?.provider !== "mock-google") {
      return anonymousSession;
    }

    return {
      mode: "mock",
      status: "authenticated",
      user: MOCK_GOOGLE_USER,
      onboarding: {
        status: parsed.onboarding?.status === "complete" ? "complete" : "in_progress",
        step: clampOnboardingStep(parsed.onboarding?.step ?? 0),
      },
    };
  } catch {
    return anonymousSession;
  }
}

function writeSession(session: AuthSession) {
  window.sessionStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session));
}

function nextAuthenticatedSession(current: AuthSession, step = current.onboarding.step): AuthSession {
  return {
    mode: "mock",
    status: "authenticated",
    user: MOCK_GOOGLE_USER,
    onboarding: {
      status: current.onboarding.status === "complete" ? "complete" : "in_progress",
      step: clampOnboardingStep(step),
    },
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState(readSession);

  const value = useMemo<AuthContextValue>(
    () => ({
      mode: session.mode,
      status: session.status,
      user: session.user,
      authenticated: session.status === "authenticated",
      onboardingComplete: session.onboarding.status === "complete",
      onboardingStep: session.onboarding.step,
      signInWithGoogle() {
        const nextSession = nextAuthenticatedSession(session, 0);
        writeSession(nextSession);
        setSession(nextSession);
      },
      setOnboardingStep(step) {
        const nextSession = nextAuthenticatedSession(session, step);
        writeSession(nextSession);
        setSession(nextSession);
      },
      finishOnboarding() {
        const nextSession: AuthSession = {
          ...nextAuthenticatedSession(session, 4),
          onboarding: {
            status: "complete",
            step: 4,
          },
        };
        writeSession(nextSession);
        setSession(nextSession);
      },
    }),
    [session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}

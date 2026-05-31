import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getMe } from "../api/authApi";
import { authConfig } from "./authConfig";
import { neonAuth, neonAuthClient } from "./neonAuthClient";
import type { AuthContextValue, AuthSession } from "./types";

const AUTH_SESSION_KEY = "job-alert.auth-session.v1";
const ONBOARDING_SESSION_KEY = "job-alert.onboarding.v1";
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

function readOnboardingState(userId: string) {
  const stored = window.sessionStorage.getItem(`${ONBOARDING_SESSION_KEY}.${userId}`);
  if (!stored) {
    return {
      status: "not_started" as const,
      step: 0,
    };
  }

  try {
    const parsed = JSON.parse(stored) as Partial<AuthSession["onboarding"]>;
    return {
      status: parsed.status === "complete" ? "complete" : "in_progress",
      step: clampOnboardingStep(parsed.step ?? 0),
    } as const;
  } catch {
    return {
      status: "not_started" as const,
      step: 0,
    };
  }
}

function writeOnboardingState(userId: string, onboarding: AuthSession["onboarding"]) {
  window.sessionStorage.setItem(`${ONBOARDING_SESSION_KEY}.${userId}`, JSON.stringify(onboarding));
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

function MockAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState(readSession);

  const value = useMemo<AuthContextValue>(
    () => ({
      mode: session.mode,
      status: session.status,
      user: session.user,
      ready: true,
      notice: authConfig.notice,
      errorMessage: null,
      authenticated: session.status === "authenticated",
      onboardingComplete: session.onboarding.status === "complete",
      onboardingStep: session.onboarding.step,
      async getIdentityToken() {
        return null;
      },
      async signInWithGoogle() {
        const nextSession = nextAuthenticatedSession(session, 0);
        writeSession(nextSession);
        setSession(nextSession);
      },
      async signOut() {
        window.sessionStorage.removeItem(AUTH_SESSION_KEY);
        setSession(anonymousSession);
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

function NeonAuthProvider({ children }: { children: ReactNode }) {
  const neonSession = neonAuthClient!.useSession();
  const [signInError, setSignInError] = useState<string | null>(null);
  const neonUser = neonSession.data?.user;
  const user = useMemo(
    () =>
      neonUser
        ? {
            id: neonUser.id,
            displayName: neonUser.name || neonUser.email,
            provider: "neon-google" as const,
          }
        : null,
    [neonUser?.email, neonUser?.id, neonUser?.name],
  );
  const [onboarding, setOnboarding] = useState(() => (user ? readOnboardingState(user.id) : anonymousSession.onboarding));

  useEffect(() => {
    let active = true;
    if (!user) return;

    neonAuth!
      .getJWTToken()
      .then((token) => {
        if (!token) return null;
        return getMe(token);
      })
      .then((me) => {
        if (!active || !me?.onboardingComplete) return;
        const completedOnboarding = {
          status: "complete" as const,
          step: 4,
        };
        writeOnboardingState(user.id, completedOnboarding);
        setOnboarding(completedOnboarding);
      })
      .catch(() => {
        // Keep the local onboarding snapshot when the API is unavailable.
      });

    return () => {
      active = false;
    };
  }, [user]);

  const activeOnboarding = useMemo(() => (user ? readOnboardingState(user.id) : onboarding), [onboarding, user]);
  const value = useMemo<AuthContextValue>(
    () => ({
      mode: "neon",
      status: neonSession.isPending ? "loading" : user ? "authenticated" : "anonymous",
      user,
      ready: !neonSession.isPending,
      notice: "Neon Auth signs into the app only. Gmail readonly connection remains a separate later step.",
      errorMessage:
        signInError ??
        (neonSession.error ? "Neon Auth session could not be loaded. Check the Auth URL and local trusted origin configuration." : null),
      authenticated: Boolean(user),
      onboardingComplete: activeOnboarding.status === "complete",
      onboardingStep: activeOnboarding.step,
      async getIdentityToken() {
        return neonAuth!.getJWTToken();
      },
      async signInWithGoogle() {
        setSignInError(null);
        try {
          await neonAuthClient!.signIn.social({
            provider: "google",
            callbackURL: "/onboarding",
          });
        } catch {
          setSignInError("Neon Auth Google sign-in could not start. Check the Auth URL and Google provider configuration.");
        }
      },
      async signOut() {
        setSignInError(null);
        await neonAuthClient!.signOut();
      },
      setOnboardingStep(step) {
        if (!user) return;
        const nextOnboarding = {
          status: "in_progress" as const,
          step: clampOnboardingStep(step),
        };
        writeOnboardingState(user.id, nextOnboarding);
        setOnboarding(nextOnboarding);
      },
      finishOnboarding() {
        if (!user) return;
        const nextOnboarding = {
          status: "complete" as const,
          step: 4,
        };
        writeOnboardingState(user.id, nextOnboarding);
        setOnboarding(nextOnboarding);
      },
    }),
    [activeOnboarding, neonSession.error, neonSession.isPending, signInError, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  if (authConfig.mode === "neon" && neonAuthClient) {
    return <NeonAuthProvider>{children}</NeonAuthProvider>;
  }

  return <MockAuthProvider>{children}</MockAuthProvider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}

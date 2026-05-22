export type AuthMode = "mock" | "neon";

export type AuthStatus = "loading" | "anonymous" | "authenticated";

export type AuthProviderId = "mock-google" | "neon-google";

export type OnboardingStatus = "not_started" | "in_progress" | "complete";

export interface AuthUser {
  id: string;
  displayName: string;
  provider: AuthProviderId;
}

export interface OnboardingState {
  status: OnboardingStatus;
  step: number;
}

export interface AuthSession {
  mode: AuthMode;
  status: AuthStatus;
  user: AuthUser | null;
  onboarding: OnboardingState;
}

export interface AuthContextValue {
  mode: AuthMode;
  status: AuthStatus;
  user: AuthUser | null;
  ready: boolean;
  notice: string | null;
  errorMessage: string | null;
  authenticated: boolean;
  onboardingComplete: boolean;
  onboardingStep: number;
  getIdentityToken: () => Promise<string | null>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  setOnboardingStep: (step: number) => void;
  finishOnboarding: () => void;
}

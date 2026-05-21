export type AuthMode = "mock";

export type AuthStatus = "anonymous" | "authenticated";

export type AuthProviderId = "mock-google";

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
  authenticated: boolean;
  onboardingComplete: boolean;
  onboardingStep: number;
  signInWithGoogle: () => void;
  setOnboardingStep: (step: number) => void;
  finishOnboarding: () => void;
}

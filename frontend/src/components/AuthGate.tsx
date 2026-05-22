import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function AuthGate({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  if (!auth.ready) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-margin_mobile">
        <div className="rounded-lg border border-surface-variant bg-surface-container-lowest px-lg py-md font-body-md text-body-md text-on-surface-variant">
          Loading app session...
        </div>
      </main>
    );
  }

  if (!auth.authenticated) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  }

  if (!auth.onboardingComplete) {
    return <Navigate replace to="/onboarding" />;
  }

  return children;
}

import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function AuthGate({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  if (!auth.authenticated) {
    return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  }

  if (!auth.onboardingComplete) {
    return <Navigate replace to="/onboarding" />;
  }

  return children;
}

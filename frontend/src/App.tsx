import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import AuthGate from "./components/AuthGate";
import DashboardApp from "./DashboardApp";
import LoginPage from "./pages/LoginPage";
import OnboardingFlow from "./pages/OnboardingFlow";
import PublicLandingPage from "./pages/PublicLandingPage";

function OnboardingRoute() {
  const auth = useAuth();
  if (!auth.ready) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-margin_mobile">
        <div className="rounded-lg border border-surface-variant bg-surface-container-lowest px-lg py-md font-body-md text-body-md text-on-surface-variant">
          Loading app session...
        </div>
      </main>
    );
  }
  if (!auth.authenticated) return <Navigate replace to="/login" />;
  if (auth.onboardingComplete) return <Navigate replace to="/app/overview" />;
  return <OnboardingFlow />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<PublicLandingPage />} path="/" />
        <Route element={<LoginPage />} path="/login" />
        <Route element={<OnboardingRoute />} path="/onboarding" />
        <Route element={<Navigate replace to="/app/overview" />} path="/app" />
        <Route
          element={
            <AuthGate>
              <DashboardApp mode="app" />
            </AuthGate>
          }
          path="/app/*"
        />
        <Route element={<Navigate replace to="/demo/overview" />} path="/demo" />
        <Route element={<DashboardApp mode="demo" />} path="/demo/*" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Routes>
    </AuthProvider>
  );
}

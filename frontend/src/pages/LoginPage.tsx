import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

export default function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  if (auth.authenticated && auth.onboardingComplete) {
    return <Navigate replace to="/app/overview" />;
  }

  if (auth.authenticated) {
    return <Navigate replace to="/onboarding" />;
  }

  function mockGoogleLogin() {
    auth.signInWithGoogle();
    navigate("/onboarding");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-margin_mobile md:p-margin_desktop">
      <section className="w-full max-w-[440px] rounded-xl bg-surface-container-lowest p-lg text-center shadow-ambient md:p-xl">
        <Link className="mx-auto mb-lg flex h-16 w-16 items-center justify-center rounded-lg bg-surface-container-low text-primary" to="/">
          <span className="material-symbols-outlined icon-fill text-[32px]">work</span>
        </Link>
        <h1 className="mb-xs font-headline-md text-headline-md text-primary">Job Alert Dashboard</h1>
        <p className="mb-md font-label-md text-label-md uppercase tracking-widest text-secondary">Automation Hub</p>
        <p className="mb-xl font-body-md text-body-md text-on-surface-variant">
          Sign in to organize job alert emails, job analysis, and application decisions.
        </p>
        <button
          className="mb-lg flex w-full items-center justify-center gap-sm rounded bg-primary-container px-lg py-[14px] font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
          onClick={mockGoogleLogin}
          type="button"
        >
          <span className="material-symbols-outlined text-[20px]">login</span>
          Continue with Google
        </button>
        <p className="mb-lg font-label-sm text-label-sm text-outline">
          AUTH0 uses a mock Google session only. Real Neon Auth login is staged for AUTH1.
        </p>
        <div className="space-y-sm rounded-lg bg-surface-container-low p-md text-left font-body-md text-body-md text-on-surface-variant">
          <p>
            <strong className="font-medium text-primary">Google login</strong> identifies your account.
          </p>
          <p>Gmail access is connected separately after login.</p>
          <p>The app requests Gmail readonly permission only when you connect Gmail.</p>
        </div>
      </section>
    </main>
  );
}

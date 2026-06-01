import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const howItWorks = [
  {
    icon: "login",
    title: "Sign in with Google",
    description: "Google login identifies the app user without an email/password account flow.",
  },
  {
    icon: "mail",
    title: "Connect Gmail job alerts",
    description: "Connect Gmail separately with readonly permission for job alert emails.",
  },
  {
    icon: "psychology",
    title: "Analyze jobs with AI",
    description: "Future backend analysis uses compact job data and an active profile summary.",
  },
  {
    icon: "task_alt",
    title: "Track decisions",
    description: "Save, ignore, or mark roles as applied while discovery stays batch-aware.",
  },
];

const privacyNotes = [
  {
    title: "Login and Gmail are separate",
    description: "Google login identifies your account. Gmail readonly access is requested only when you connect job alerts.",
  },
  {
    title: "Browser secrets stay out",
    description: "The frontend never receives AI API keys or database credentials and never connects directly to Neon.",
  },
  {
    title: "Compact analysis context",
    description: "Profile summaries support matching. Raw Gmail bodies are not sent for AI analysis.",
  },
  {
    title: "Resume handling",
    description: "Resume PDFs are managed separately and are not sent for AI analysis by default.",
  },
];

function PublicActionButtons({ onGoogle }: { onGoogle: () => void }) {
  return (
    <div className="flex w-full flex-col items-center justify-center gap-md sm:flex-row">
      <button
        className="flex w-full items-center justify-center gap-sm rounded-lg bg-primary-container px-lg py-md font-label-md text-label-md text-on-primary shadow-ambient transition-opacity hover:opacity-90 sm:w-auto"
        onClick={onGoogle}
        type="button"
      >
        <span className="material-symbols-outlined text-[20px]">login</span>
        Continue with Google
      </button>
      <Link
        className="flex w-full items-center justify-center gap-sm rounded-lg border border-outline-variant bg-surface-container-lowest px-lg py-md font-label-md text-label-md text-primary transition-colors hover:bg-surface-container-low sm:w-auto"
        to="/demo"
      >
        <span className="material-symbols-outlined text-[20px]">dashboard</span>
        View demo dashboard
      </Link>
    </div>
  );
}

export default function PublicLandingPage() {
  const auth = useAuth();
  const navigate = useNavigate();

  async function beginSignIn() {
    await auth.signInWithGoogle();
    if (auth.mode === "mock") {
      navigate("/onboarding");
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-background">
      <nav className="sticky top-0 z-40 border-b border-outline-variant/30 bg-surface-container-lowest shadow-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-margin_mobile md:px-margin_desktop">
          <Link className="flex items-center gap-sm text-primary" to="/">
            <span className="material-symbols-outlined text-[24px]">work</span>
            <span className="font-headline-sm text-headline-sm">Job Alert Dashboard</span>
          </Link>
          <div className="hidden items-center gap-lg md:flex">
            <a className="font-body-md text-body-md text-on-surface-variant transition-colors hover:text-primary" href="#how-it-works">
              How it works
            </a>
            <a className="font-body-md text-body-md text-on-surface-variant transition-colors hover:text-primary" href="#privacy">
              Privacy
            </a>
            <Link className="font-body-md text-body-md text-on-surface-variant transition-colors hover:text-primary" to="/login">
              Login
            </Link>
            <button
              className="flex items-center gap-xs rounded bg-primary-container px-md py-sm font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
              onClick={() => void beginSignIn()}
              type="button"
            >
              <span className="material-symbols-outlined text-[18px]">login</span>
              Continue with Google
            </button>
          </div>
        </div>
      </nav>

      <main>
        <section className="mx-auto flex w-full max-w-4xl flex-col items-center px-margin_mobile pb-16 pt-20 text-center md:px-margin_desktop">
          <h1 className="mb-lg max-w-3xl font-display-lg text-display-lg leading-tight text-primary">
            Organize job alerts and focus on the opportunities that fit.
          </h1>
          <p className="mb-xl max-w-2xl font-body-lg text-body-lg text-on-surface-variant">
            Collect job alert emails, analyze roles, and track application decisions in one calm dashboard.
          </p>
          <PublicActionButtons onGoogle={() => void beginSignIn()} />
          <p className="mt-sm font-label-sm text-label-sm text-on-surface-variant opacity-70">
            Gmail access is connected separately after login.
          </p>
          {auth.notice ? <p className="mt-sm rounded bg-surface-container-low px-md py-sm font-label-sm text-label-sm text-on-surface-variant">{auth.notice}</p> : null}
        </section>

        <section className="mx-auto w-full max-w-6xl px-margin_mobile pb-24 md:px-margin_desktop">
          <div className="flex w-full flex-col gap-lg rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-lg shadow-ambient md:p-xl">
            <div className="flex items-center justify-between border-b border-outline-variant/20 pb-md">
              <h2 className="font-headline-sm text-headline-sm text-primary">Overview</h2>
              <span className="material-symbols-outlined text-on-surface-variant">more_horiz</span>
            </div>
            <div className="grid grid-cols-1 gap-gutter md:grid-cols-12">
              <div className="flex flex-col gap-sm md:col-span-3">
                {[
                  ["New Jobs", "12", "work"],
                  ["Newly Discovered", "8", "new_releases"],
                  ["Likely Relevant", "5", "filter_alt"],
                  ["AI High Priority", "3", "psychology"],
                  ["Saved", "4", "bookmark"],
                  ["Applied", "2", "task_alt"],
                ].map(([label, value, icon], index) => (
                  <div
                    className={`flex items-center justify-between rounded p-md ${
                      index === 1 ? "border border-secondary-container bg-secondary-container/30" : "bg-surface-container-low"
                    }`}
                    key={label}
                  >
                    <span className="flex items-center gap-xs font-label-md text-label-md text-on-surface-variant">
                      <span className="material-symbols-outlined text-[16px]">{icon}</span>
                      {label}
                    </span>
                    <span className="font-label-md text-label-md font-bold text-primary">{value}</span>
                  </div>
                ))}
              </div>
              <div className="flex flex-col gap-gutter md:col-span-9">
                <article className="relative rounded-lg border border-outline-variant/30 border-l-4 border-l-secondary bg-surface-container-lowest p-lg">
                  <div className="mb-sm flex flex-wrap gap-xs md:absolute md:right-md md:top-md">
                    <span className="rounded bg-secondary-container px-2 py-1 font-label-sm text-label-sm text-on-secondary-container">8.8 fit</span>
                    <span className="rounded bg-surface-container-high px-2 py-1 font-label-sm text-label-sm text-on-surface-variant">New in this run</span>
                  </div>
                  <h3 className="mb-xs font-headline-sm text-headline-sm text-primary md:pr-36">Werkstudent KI &amp; Automatisierung</h3>
                  <div className="mb-md flex flex-wrap items-center gap-sm font-body-md text-body-md text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">domain</span>
                    Northstar Grid Labs
                    <span className="text-outline-variant">•</span>
                    <span className="material-symbols-outlined text-[18px]">location_on</span>
                    Berlin / Hybrid
                  </div>
                  <p className="mb-md max-w-2xl font-body-md text-body-md text-on-surface-variant">
                    Compact job details, rule matches, analysis reasons, concerns, and application links stay reviewable in one workspace.
                  </p>
                  <div className="flex flex-wrap gap-sm">
                    <button className="rounded bg-surface-container px-sm py-xs font-label-md text-label-md text-on-surface" type="button">
                      Save
                    </button>
                    <button className="rounded bg-surface-container px-sm py-xs font-label-md text-label-md text-on-surface" type="button">
                      Mark Applied
                    </button>
                    <button className="rounded bg-surface-container px-sm py-xs font-label-md text-label-md text-on-surface" type="button">
                      Ignore
                    </button>
                  </div>
                </article>
                <article className="rounded-lg border border-outline-variant/30 bg-surface-container-lowest p-lg opacity-75">
                  <h3 className="mb-xs font-headline-sm text-headline-sm text-primary">Working Student Data &amp; Automation</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant">CloudHarbor Analytics • Remote • StepStone</p>
                </article>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-outline-variant/20 bg-surface-container-low px-margin_mobile py-20 md:px-margin_desktop" id="how-it-works">
          <div className="mx-auto w-full max-w-6xl">
            <h2 className="mb-xl text-center font-display-lg text-display-lg text-primary">How it works</h2>
            <div className="grid grid-cols-1 gap-gutter md:grid-cols-2 lg:grid-cols-4">
              {howItWorks.map((item) => (
                <article className="flex flex-col items-start gap-md rounded-lg bg-surface-container-lowest p-lg shadow-ambient" key={item.title}>
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-container">
                    <span className="material-symbols-outlined text-primary">{item.icon}</span>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-primary">{item.title}</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant">{item.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-b border-outline-variant/20 bg-surface-container-lowest px-margin_mobile py-20 md:px-margin_desktop" id="privacy">
          <div className="mx-auto w-full max-w-5xl">
            <div className="mb-lg flex items-center gap-sm">
              <span className="material-symbols-outlined text-[32px] text-primary">shield_lock</span>
              <h2 className="font-display-lg text-display-lg text-primary">Privacy &amp; Security</h2>
            </div>
            <div className="grid grid-cols-1 gap-md md:grid-cols-2">
              {privacyNotes.map((item) => (
                <article className="rounded-lg border border-outline-variant/20 bg-surface p-md" key={item.title}>
                  <h3 className="mb-xs font-headline-sm text-headline-sm text-primary">{item.title}</h3>
                  <p className="font-body-md text-body-md text-on-surface-variant">{item.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto flex w-full max-w-3xl flex-col items-center px-margin_mobile py-24 text-center md:px-margin_desktop">
          <h2 className="mb-lg font-display-lg text-display-lg text-primary">Start with your existing job alerts.</h2>
          <PublicActionButtons onGoogle={() => void beginSignIn()} />
          <p className="mt-md font-body-md text-body-md text-on-surface-variant">No email/password account required.</p>
        </section>
      </main>
    </div>
  );
}

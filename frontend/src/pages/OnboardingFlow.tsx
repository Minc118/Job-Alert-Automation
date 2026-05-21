import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";

const steps = ["Welcome", "Preferences", "Connect Gmail", "Profile & Resume", "Finish"] as const;

const preferenceGroups = [
  { label: "Target roles", values: ["Werkstudent AI", "Working Student Software Engineering", "Project Coordinator"] },
  { label: "Preferred locations", values: ["Berlin", "Potsdam", "Remote", "Hybrid Berlin"] },
  { label: "Excluded keywords", values: ["senior", "lead", "internship unpaid"] },
];

function StepBody({ step }: { step: number }) {
  if (step === 0) {
    return (
      <>
        <span className="material-symbols-outlined flex h-20 w-20 items-center justify-center rounded-full bg-surface-container text-[40px] text-primary">work</span>
        <h1 className="font-headline-md text-headline-md text-primary">Welcome to Job Alert Dashboard</h1>
        <p className="max-w-lg font-body-lg text-body-lg text-on-surface-variant">
          Collect job alert emails, analyze roles, and manage application decisions without mixing discovery batches with your saved/applied status.
        </p>
      </>
    );
  }

  if (step === 1) {
    return (
      <div className="w-full space-y-md text-left">
        <div className="text-center">
          <h1 className="font-headline-md text-headline-md text-primary">Set job preferences</h1>
          <p className="mt-sm font-body-md text-body-md text-on-surface-variant">Mock examples now; editable auth-scoped preferences arrive in a later phase.</p>
        </div>
        {preferenceGroups.map((group) => (
          <section className="rounded-lg border border-surface-variant bg-surface-container-low p-md" key={group.label}>
            <div className="mb-sm font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">{group.label}</div>
            <div className="flex flex-wrap gap-sm">
              {group.values.map((value) => (
                <span className="rounded-full bg-surface-container-lowest px-3 py-1 font-label-md text-label-md text-primary" key={value}>
                  {value}
                </span>
              ))}
            </div>
          </section>
        ))}
      </div>
    );
  }

  if (step === 2) {
    return (
      <>
        <span className="material-symbols-outlined flex h-24 w-24 items-center justify-center rounded-full border border-surface-variant bg-surface-container-low text-[40px] text-primary">mail</span>
        <h1 className="font-headline-md text-headline-md text-primary">Connect Gmail separately</h1>
        <p className="max-w-lg font-body-lg text-body-lg text-on-surface-variant">
          Google login does not grant email access. Gmail connection will request readonly permission for job alert messages from LinkedIn, StepStone, and Indeed.
        </p>
        <button className="rounded-lg bg-primary-container px-lg py-md font-label-md text-label-md text-on-primary opacity-80" type="button">
          Connect Gmail
        </button>
        <p className="font-label-sm text-label-sm text-outline">Mock onboarding step only. Scope planned: gmail.readonly.</p>
      </>
    );
  }

  if (step === 3) {
    return (
      <div className="w-full space-y-md text-left">
        <div className="text-center">
          <h1 className="font-headline-md text-headline-md text-primary">Profile &amp; Resume</h1>
          <p className="mt-sm font-body-md text-body-md text-on-surface-variant">
            Profile summaries help job matching. Resume PDFs are reserved for future application material generation.
          </p>
        </div>
        {[
          ["description", "Profile summary markdown", "Used as compact job matching context."],
          ["picture_as_pdf", "Resume PDF", "Stored separately and not sent to Gemini by default."],
        ].map(([icon, title, description]) => (
          <section className="flex flex-col gap-md rounded-lg border border-surface-variant bg-surface-container-low p-md sm:flex-row sm:items-center sm:justify-between" key={title}>
            <div className="flex gap-sm">
              <span className="material-symbols-outlined text-primary">{icon}</span>
              <div>
                <h2 className="font-body-lg text-body-lg font-medium text-primary">{title}</h2>
                <p className="font-body-md text-body-md text-on-surface-variant">{description}</p>
              </div>
            </div>
            <button className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm font-label-md text-label-md text-primary" type="button">
              Upload later
            </button>
          </section>
        ))}
      </div>
    );
  }

  return (
    <>
      <span className="material-symbols-outlined icon-fill flex h-20 w-20 items-center justify-center rounded-full bg-secondary-container text-[40px] text-on-secondary-container">task_alt</span>
      <h1 className="font-headline-md text-headline-md text-primary">Setup complete</h1>
      <p className="max-w-lg font-body-lg text-body-lg text-on-surface-variant">
        The dashboard can now open with mock setup state. Real Google auth, Gmail connection, and Gemini analysis stay staged for later phases.
      </p>
    </>
  );
}

export default function OnboardingFlow() {
  const auth = useAuth();
  const navigate = useNavigate();
  const step = auth.onboardingStep;
  const finalStep = step === steps.length - 1;

  function goForward() {
    if (!finalStep) {
      auth.setOnboardingStep(step + 1);
      return;
    }
    auth.finishOnboarding();
    navigate("/app/overview");
  }

  function goBack() {
    auth.setOnboardingStep(step - 1);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-margin_mobile md:p-margin_desktop">
      <section className="relative flex w-full max-w-3xl flex-col gap-xl overflow-hidden rounded-xl border border-surface-container bg-surface-container-lowest p-lg shadow-sm md:p-xl">
        <div aria-label="Onboarding progress" className="grid grid-cols-5 gap-sm">
          {steps.map((label, index) => (
            <div className="space-y-xs" key={label}>
              <div className={`h-1 rounded-full ${index <= step ? "bg-primary" : "bg-surface-container-highest"}`} />
              <span className={`hidden text-center font-label-sm text-label-sm md:block ${index === step ? "font-bold text-primary" : "text-outline"}`}>{label}</span>
            </div>
          ))}
        </div>
        <div className="z-10 flex min-h-[360px] flex-col items-center justify-center gap-md text-center">
          <StepBody step={step} />
        </div>
        <p className="z-10 font-label-sm text-label-sm text-outline">
          Mock setup state is stored for this browser session only until real Google auth and backend onboarding state are added.
        </p>
        <div className="z-10 flex items-center justify-between border-t border-surface-container-highest pt-lg">
          <button
            className="rounded-md px-sm py-2 font-label-md text-label-md text-on-surface-variant transition-colors hover:bg-surface-container-low hover:text-primary disabled:opacity-40"
            disabled={step === 0}
            onClick={goBack}
            type="button"
          >
            Back
          </button>
          <button
            className="flex items-center gap-xs rounded-lg bg-primary-container px-lg py-md font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90"
            onClick={goForward}
            type="button"
          >
            {finalStep ? "Go to Dashboard" : "Continue"}
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          </button>
        </div>
      </section>
    </main>
  );
}

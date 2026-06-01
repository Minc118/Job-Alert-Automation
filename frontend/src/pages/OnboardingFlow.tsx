import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  completeAuthenticatedOnboarding,
  getAuthenticatedPreferences,
  startAuthenticatedGmailConnect,
  updateAuthenticatedPreferences,
} from "../api/authApi";
import { useAuth } from "../auth/AuthProvider";

const steps = ["Welcome", "Preferences", "Connect Gmail", "Profile & Resume", "Finish"] as const;

const defaultPreferenceText = {
  targetRoleKeywords: "Werkstudent AI, Working Student Software Engineering, Project Coordinator",
  preferredLocations: "Berlin, Potsdam, Remote, Hybrid Berlin",
  excludedKeywords: "senior, lead, internship unpaid",
};

function splitTerms(value: string) {
  return value
    .split(/[\n,]/)
    .map((term) => term.trim())
    .filter(Boolean);
}

function StepBody({
  step,
  preferenceText,
  onPreferenceTextChange,
  gmailConnectEnabled,
  gmailConnecting,
  gmailNotice,
  onConnectGmail,
}: {
  step: number;
  preferenceText: typeof defaultPreferenceText;
  onPreferenceTextChange: (field: keyof typeof defaultPreferenceText, value: string) => void;
  gmailConnectEnabled: boolean;
  gmailConnecting: boolean;
  gmailNotice: string | null;
  onConnectGmail: () => void;
}) {
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
          <p className="mt-sm font-body-md text-body-md text-on-surface-variant">Use commas or new lines. These terms shape future job filtering and matching.</p>
        </div>
        <PreferenceTextArea
          label="Target roles"
          onChange={(value) => onPreferenceTextChange("targetRoleKeywords", value)}
          value={preferenceText.targetRoleKeywords}
        />
        <PreferenceTextArea
          label="Preferred locations"
          onChange={(value) => onPreferenceTextChange("preferredLocations", value)}
          value={preferenceText.preferredLocations}
        />
        <PreferenceTextArea
          label="Excluded keywords"
          onChange={(value) => onPreferenceTextChange("excludedKeywords", value)}
          value={preferenceText.excludedKeywords}
        />
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
        <button
          className="rounded-lg bg-primary-container px-lg py-md font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!gmailConnectEnabled || gmailConnecting}
          onClick={onConnectGmail}
          type="button"
        >
          {gmailConnecting ? "Starting Gmail..." : "Connect Gmail"}
        </button>
        <p className="font-label-sm text-label-sm text-outline">
          {gmailConnectEnabled
            ? "The backend starts Gmail OAuth with gmail.readonly scope."
            : "Mock onboarding keeps Gmail authorization UI-only."}
        </p>
        {gmailNotice ? (
          <p className="max-w-lg rounded-lg border border-error-container bg-surface px-md py-sm font-body-md text-body-md text-on-error-container">
            {gmailNotice}
          </p>
        ) : null}
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
          ["picture_as_pdf", "Resume PDF", "Stored separately and not sent for AI analysis by default."],
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
        The dashboard can now open with saved setup state. Gmail connection, profile upload, and AI analysis stay staged for later phases.
      </p>
    </>
  );
}

export default function OnboardingFlow() {
  const auth = useAuth();
  const navigate = useNavigate();
  const step = auth.onboardingStep;
  const finalStep = step === steps.length - 1;
  const [preferenceText, setPreferenceText] = useState(defaultPreferenceText);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [gmailConnecting, setGmailConnecting] = useState(false);
  const [gmailNotice, setGmailNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (auth.mode !== "neon" || !auth.authenticated) return;
    auth
      .getIdentityToken()
      .then((token) => {
        if (!token) return null;
        return getAuthenticatedPreferences(token);
      })
      .then((preferences) => {
        if (!active || !preferences) return;
        setPreferenceText({
          targetRoleKeywords: preferences.targetRoleKeywords.join(", ") || defaultPreferenceText.targetRoleKeywords,
          preferredLocations: preferences.preferredLocations.join(", ") || defaultPreferenceText.preferredLocations,
          excludedKeywords: preferences.excludedKeywords.join(", ") || defaultPreferenceText.excludedKeywords,
        });
      })
      .catch(() => {
        if (active) setSaveError("Saved preferences could not be loaded. You can continue with these values and retry.");
      });

    return () => {
      active = false;
    };
  }, [auth]);

  async function savePreferences() {
    if (auth.mode !== "neon") return;
    const token = await auth.getIdentityToken();
    if (!token) throw new Error("Missing identity token.");
    await updateAuthenticatedPreferences(token, {
      targetRoleKeywords: splitTerms(preferenceText.targetRoleKeywords),
      preferredLocations: splitTerms(preferenceText.preferredLocations),
      excludedKeywords: splitTerms(preferenceText.excludedKeywords),
    });
  }

  async function connectGmail() {
    if (auth.mode !== "neon") return;
    setGmailConnecting(true);
    setGmailNotice(null);
    try {
      const token = await auth.getIdentityToken();
      if (!token) throw new Error("Missing identity token.");
      const { authorizationUrl } = await startAuthenticatedGmailConnect(token);
      window.location.assign(authorizationUrl);
    } catch {
      setGmailNotice("Gmail connection could not be started. Check the local API and Gmail OAuth configuration.");
      setGmailConnecting(false);
    }
  }

  async function goForward() {
    setSaveError(null);
    setSaving(true);
    try {
      if (step === 1) {
        await savePreferences();
      }
      if (!finalStep) {
        auth.setOnboardingStep(step + 1);
        return;
      }
      if (auth.mode === "neon") {
        const token = await auth.getIdentityToken();
        if (!token) throw new Error("Missing identity token.");
        await completeAuthenticatedOnboarding(token);
      }
      auth.finishOnboarding();
      navigate("/app/overview");
    } catch {
      setSaveError("Setup could not be saved. Check the local API and backend auth configuration, then retry.");
    } finally {
      setSaving(false);
    }
  }

  function goBack() {
    auth.setOnboardingStep(step - 1);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-margin_mobile md:p-margin_desktop">
      <section className="relative flex w-full max-w-3xl flex-col gap-xl overflow-hidden rounded-xl border border-surface-container bg-surface-container-lowest p-lg shadow-sm md:p-xl">
        <Link className="z-10 inline-flex w-fit items-center gap-sm font-label-md text-label-md text-primary hover:opacity-80" to="/">
          <span className="material-symbols-outlined text-[18px]">work</span>
          Job Alert Dashboard
        </Link>
        <div aria-label="Onboarding progress" className="grid grid-cols-5 gap-sm">
          {steps.map((label, index) => (
            <div className="space-y-xs" key={label}>
              <div className={`h-1 rounded-full ${index <= step ? "bg-primary" : "bg-surface-container-highest"}`} />
              <span className={`hidden text-center font-label-sm text-label-sm md:block ${index === step ? "font-bold text-primary" : "text-outline"}`}>{label}</span>
            </div>
          ))}
        </div>
        <div className="z-10 flex min-h-[360px] flex-col items-center justify-center gap-md text-center">
          <StepBody
            onPreferenceTextChange={(field, value) => setPreferenceText((current) => ({ ...current, [field]: value }))}
            preferenceText={preferenceText}
            step={step}
            gmailConnectEnabled={auth.mode === "neon" && auth.authenticated}
            gmailConnecting={gmailConnecting}
            gmailNotice={gmailNotice}
            onConnectGmail={() => void connectGmail()}
          />
        </div>
        <p className="z-10 font-label-sm text-label-sm text-outline">
          {auth.mode === "neon"
            ? "Preferences and setup completion are saved through the local API. Gmail readonly connect can start here; document uploads stay in Settings."
            : "Mock setup state is stored for this browser session only until real Google auth and backend onboarding state are added."}
        </p>
        {saveError ? (
          <p className="z-10 rounded-lg border border-error-container bg-surface px-md py-sm font-body-md text-body-md text-on-error-container">
            {saveError}
          </p>
        ) : null}
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
            disabled={saving}
            onClick={() => void goForward()}
            type="button"
          >
            {saving ? "Saving..." : finalStep ? "Go to Dashboard" : "Continue"}
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
          </button>
        </div>
      </section>
    </main>
  );
}

function PreferenceTextArea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block rounded-lg border border-surface-variant bg-surface-container-low p-md">
      <span className="mb-sm block font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">{label}</span>
      <textarea
        className="min-h-20 w-full rounded-md border border-outline-variant bg-surface-container-lowest px-md py-sm font-body-md text-body-md text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      />
    </label>
  );
}

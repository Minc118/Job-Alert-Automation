export default function SystemNotesCard() {
  return (
    <section className="flex items-start gap-4 rounded-lg border border-secondary-fixed-dim bg-secondary-container p-md md:p-lg lg:col-span-12">
      <span className="material-symbols-outlined icon-fill mt-1 text-on-secondary-container">info</span>
      <div>
        <h4 className="mb-2 font-headline-sm text-headline-sm text-on-secondary-container">System Operation Notes</h4>
        <p className="max-w-4xl font-body-md text-body-md text-on-secondary-container opacity-90">
          This dashboard is a local manual workflow. Job data will come from the local backend API, which reads Neon.
          The browser never receives database credentials, private files, Gmail tokens, or AI API keys. Codex analysis is
          prepared and imported manually.
        </p>
      </div>
    </section>
  );
}

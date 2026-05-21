export default function GPTApplicationPromptBox({ prompt }: { prompt: string }) {
  async function copyPrompt() {
    if (!navigator.clipboard) return;
    await navigator.clipboard.writeText(prompt);
  }

  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h4 className="font-label-md text-label-md font-bold text-primary">GPT Application Prompt</h4>
        <button
          className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-secondary transition-colors hover:text-primary"
          onClick={copyPrompt}
          type="button"
        >
          <span className="material-symbols-outlined text-[14px]">content_copy</span>
          Copy
        </button>
      </div>
      <div className="relative max-h-32 overflow-hidden rounded-lg border border-outline-variant/20 bg-primary-container p-3 font-mono text-[12px] leading-relaxed text-on-primary-container">
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-primary-container to-transparent" />
        {prompt}
      </div>
    </section>
  );
}

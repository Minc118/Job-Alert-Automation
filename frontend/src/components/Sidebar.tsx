import type { Page } from "../types";

const navItems: Array<{ page: Page; label: string; icon: string }> = [
  { page: "overview", label: "Overview", icon: "dashboard" },
  { page: "jobs", label: "Jobs", icon: "work" },
  { page: "settings", label: "Settings", icon: "settings" },
];

export default function Sidebar({ page, onNavigate }: { page: Page; onNavigate: (page: Page) => void }) {
  return (
    <nav className="fixed left-0 top-0 z-50 hidden h-screen w-64 flex-col gap-sm border-r border-outline-variant bg-surface-container-low py-lg md:flex">
      <div className="px-5 pb-6">
        <h1 className="font-headline-sm text-headline-sm font-bold text-primary">Job Alert Dashboard</h1>
        <p className="mt-1 font-label-md text-label-md text-on-surface-variant">Automation Hub</p>
      </div>
      <div className="px-5">
        <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary-container px-4 py-2 font-label-md text-label-md text-on-primary transition-opacity hover:opacity-90">
          <span className="material-symbols-outlined text-[18px]">sync</span>
          Run Fetch
        </button>
      </div>
      <div className="mt-4 flex flex-1 flex-col gap-1">
        {navItems.map((item) => {
          const active = page === item.page;
          return (
            <button
              className={`flex items-center gap-3 py-3 text-left font-label-md text-label-md transition-all duration-200 ${
                active
                  ? "border-l-4 border-primary bg-surface-container-high pl-4 font-bold text-primary"
                  : "pl-5 text-on-surface-variant hover:bg-surface-container"
              }`}
              key={item.page}
              onClick={() => onNavigate(item.page)}
              type="button"
            >
              <span className={`material-symbols-outlined ${active ? "icon-fill" : ""}`}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </div>
      <div className="mt-auto px-5">
        <div className="rounded-lg border border-surface-variant bg-surface p-3 font-label-sm text-label-sm text-on-surface-variant">
          Local manual workflow. No browser-side database or AI credentials.
        </div>
      </div>
    </nav>
  );
}

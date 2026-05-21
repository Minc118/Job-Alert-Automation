import type { ReactNode } from "react";

export default function SettingsSection({
  title,
  icon,
  children,
  className = "",
}: {
  title: string;
  icon: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-surface-variant bg-surface-container-lowest p-lg shadow-sm ${className}`}>
      <div className="mb-6 flex items-center gap-2">
        <span className="material-symbols-outlined text-surface-tint">{icon}</span>
        <h3 className="font-headline-sm text-headline-sm text-primary">{title}</h3>
      </div>
      {children}
    </section>
  );
}

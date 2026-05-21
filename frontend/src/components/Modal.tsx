import type { ReactNode } from "react";

export default function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-primary/40 p-4">
      <div className="w-full max-w-lg overflow-hidden rounded-xl border border-surface-variant bg-surface-container-lowest shadow-lg">
        <div className="flex items-center justify-between border-b border-surface-variant bg-surface-bright p-4">
          <h3 className="font-headline-sm text-headline-sm text-primary">{title}</h3>
          <button className="rounded-full p-1 text-on-surface-variant hover:bg-surface-container" onClick={onClose} type="button">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

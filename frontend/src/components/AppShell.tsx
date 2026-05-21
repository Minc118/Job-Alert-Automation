import type { ReactNode } from "react";
import type { Page, User, UserId } from "../types";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

const mobileItems: Array<{ page: Page; label: string; icon: string }> = [
  { page: "overview", label: "Overview", icon: "dashboard" },
  { page: "jobs", label: "Jobs", icon: "work" },
  { page: "settings", label: "Settings", icon: "settings" },
];

export default function AppShell({
  children,
  page,
  users,
  selectedUserId,
  onNavigate,
  onRefreshData,
  onUserChange,
}: {
  children: ReactNode;
  page: Page;
  users: User[];
  selectedUserId: UserId;
  onNavigate: (page: Page) => void;
  onRefreshData: () => void | Promise<void>;
  onUserChange: (userId: UserId) => void;
}) {
  return (
    <div className="min-h-screen bg-background text-on-background">
      <Sidebar onNavigate={onNavigate} page={page} />
      <div className="flex min-h-screen flex-col md:ml-64">
        <Topbar
          onRefreshData={onRefreshData}
          onUserChange={onUserChange}
          page={page}
          selectedUserId={selectedUserId}
          users={users}
        />
        {children}
      </div>
      <nav className="fixed bottom-0 left-0 z-50 flex h-16 w-full items-center justify-around border-t border-outline-variant bg-surface px-2 md:hidden">
        {mobileItems.map((item) => {
          const active = page === item.page;
          return (
            <button
              className={`flex h-full w-full flex-col items-center justify-center transition-opacity active:opacity-80 ${
                active ? "font-bold text-primary" : "text-on-surface-variant"
              }`}
              key={item.page}
              onClick={() => onNavigate(item.page)}
              type="button"
            >
              <span className={`material-symbols-outlined mb-1 ${active ? "rounded-full bg-primary-container px-4 py-1 text-on-primary-container" : ""}`}>
                {item.icon}
              </span>
              <span className="font-label-sm text-[10px]">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}

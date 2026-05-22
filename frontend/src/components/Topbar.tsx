import { Link } from "react-router-dom";
import type { Page, User, UserId } from "../types";

const titles: Record<Page, string> = {
  overview: "Overview",
  jobs: "Jobs",
  settings: "Settings",
};

export default function Topbar({
  page,
  users,
  selectedUserId,
  onRefreshData,
  onUserChange,
  signedInDisplayName,
  showRefreshData,
  showUserSwitcher,
}: {
  page: Page;
  users: User[];
  selectedUserId: UserId;
  onRefreshData: () => void | Promise<void>;
  onUserChange: (userId: UserId) => void;
  signedInDisplayName?: string;
  showRefreshData: boolean;
  showUserSwitcher: boolean;
}) {
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between bg-surface px-margin_mobile shadow-sm md:px-margin_desktop">
      <div className="flex items-center gap-4">
        <Link className="flex items-center gap-2 text-primary md:hidden" to="/">
          <span className="material-symbols-outlined text-[18px]">work</span>
          <span className="font-label-md text-label-md">Job Alert Dashboard</span>
        </Link>
        <span className="font-headline-md-mobile text-headline-md-mobile text-primary md:hidden">{titles[page]}</span>
      </div>
      <div className="flex items-center gap-3">
        {showRefreshData ? (
          <>
            <button
              className="hidden items-center gap-2 rounded-full p-2 font-label-md text-label-md text-on-surface-variant transition-colors hover:bg-surface-container-high md:flex"
              onClick={() => void onRefreshData()}
              type="button"
            >
              <span className="material-symbols-outlined">sync</span>
              Refresh Data
            </button>
            <div className="hidden items-center gap-2 rounded-full bg-surface-container-low px-3 py-1.5 md:flex">
              <span className="h-2 w-2 rounded-full bg-primary" />
              <span className="font-label-sm text-label-sm text-on-surface-variant">Latest Run</span>
            </div>
          </>
        ) : null}
        {showUserSwitcher ? (
          <select
            className="rounded-full border border-outline-variant bg-surface-container-low px-3 py-1.5 font-label-md text-label-md text-primary outline-none focus:border-primary focus:ring-1 focus:ring-primary"
            onChange={(event) => onUserChange(event.target.value as UserId)}
            value={selectedUserId}
          >
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.displayName}
              </option>
            ))}
          </select>
        ) : (
          <span className="max-w-[180px] truncate rounded-full border border-outline-variant bg-surface-container-low px-3 py-1.5 font-label-md text-label-md text-primary">
            {signedInDisplayName ?? "Signed in"}
          </span>
        )}
      </div>
    </header>
  );
}

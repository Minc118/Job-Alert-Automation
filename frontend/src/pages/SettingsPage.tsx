import type { DataSourceStatus, User, UserDocument, UserPreferences } from "../types";
import DataSourceStatusCard from "../components/DataSourceStatusCard";
import GmailConnectionPanel from "../components/GmailConnectionPanel";
import ProfileResumeSection from "../components/ProfileResumeSection";
import SettingsSection from "../components/SettingsSection";
import SystemNotesCard from "../components/SystemNotesCard";

export default function SettingsPage({
  user,
  preferences,
  documents,
  dataSources,
}: {
  user: User;
  preferences: UserPreferences;
  documents: UserDocument[];
  dataSources: DataSourceStatus[];
}) {
  return (
    <main className="flex-1 p-margin_mobile pb-24 md:p-margin_desktop">
      <div className="mb-xl">
        <h2 className="mb-2 font-display-lg text-display-lg text-primary">Settings</h2>
        <p className="font-body-lg text-body-lg text-on-surface-variant">Manage local search configuration and mock integrations.</p>
      </div>

      <div className="grid grid-cols-1 gap-gutter lg:grid-cols-12">
        <SettingsSection className="lg:col-span-12" icon="manage_accounts" title="User Preferences">
          <div className="grid grid-cols-1 gap-xl md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Display Name</span>
              <div className="border-b border-surface-variant pb-2 font-body-lg text-body-lg text-on-surface">{user.displayName}</div>
            </div>
            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Preferred Locations</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {preferences.preferredLocations.map((location) => (
                  <span className="rounded-full bg-secondary-container px-3 py-1 font-label-md text-label-md text-on-secondary-fixed-variant" key={location}>
                    {location}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-2 md:col-span-2">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">Target Role Keywords</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {preferences.targetRoleKeywords.map((keyword) => (
                  <span className="rounded-DEFAULT bg-surface-container px-3 py-1 font-label-md text-label-md text-on-surface" key={keyword}>
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </SettingsSection>

        <GmailConnectionPanel />

        <ProfileResumeSection documents={documents} />

        <SettingsSection className="flex flex-col lg:col-span-6" icon="database" title="Data Sources">
          <div className="flex-1 overflow-hidden rounded-DEFAULT border border-surface-variant">
            {dataSources.map((source) => (
              <DataSourceStatusCard key={source.source} source={source} />
            ))}
          </div>
        </SettingsSection>

        <SystemNotesCard />
      </div>
    </main>
  );
}

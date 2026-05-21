import type { UserDocument } from "../types";
import PrivateProfileFileStatus from "./PrivateProfileFileStatus";
import SettingsSection from "./SettingsSection";

export default function ProfileResumeSection({ documents }: { documents: UserDocument[] }) {
  return (
    <SettingsSection className="lg:col-span-6" icon="folder_open" title="Profile & Resume">
      <p className="mb-6 border-b border-surface-variant pb-4 font-body-md text-body-md text-on-surface-variant">
        Files stay local under private/. This mock UI does not read, upload, or expose private file contents.
      </p>
      <div className="flex flex-col gap-4">
        {documents.map((document) => (
          <PrivateProfileFileStatus document={document} key={document.id} />
        ))}
      </div>
    </SettingsSection>
  );
}

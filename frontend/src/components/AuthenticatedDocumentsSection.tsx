import type { AuthenticatedDocument, AuthenticatedDocumentPreview } from "../api/authApi";
import SettingsSection from "./SettingsSection";

const managedDocumentTypes = [
  {
    type: "profile_markdown" as const,
    title: "Profile Summary",
    accept: ".md,.markdown,text/markdown,text/plain",
    icon: "description",
    note: "Active Markdown summary used for AI job matching.",
  },
  {
    type: "resume_pdf" as const,
    title: "Resume PDF",
    accept: ".pdf,application/pdf",
    icon: "picture_as_pdf",
    note: "Stored privately for future application material work.",
  },
];

function formatSize(bytes: number | null) {
  if (bytes == null) return "";
  if (bytes < 1024) return `${bytes} B`;
  return `${Math.round(bytes / 1024)} KB`;
}

export default function AuthenticatedDocumentsSection({
  documents,
  loading,
  notice,
  preview,
  onActivate,
  onDelete,
  onPreview,
  onUpload,
}: {
  documents: AuthenticatedDocument[];
  loading: boolean;
  notice: string | null;
  preview: AuthenticatedDocumentPreview | null;
  onActivate: (documentId: number) => void;
  onDelete: (documentId: number) => void;
  onPreview: (documentId: number) => void;
  onUpload: (documentType: AuthenticatedDocument["documentType"], file: File) => void;
}) {
  return (
    <SettingsSection className="lg:col-span-12" icon="folder_open" title="Profile & Resume">
      <div className="space-y-md">
        <p className="max-w-4xl font-body-md text-body-md text-on-surface-variant">
          Files are uploaded to private backend storage. The browser receives safe metadata only; resume PDFs are not sent for AI analysis by default.
        </p>
        {notice ? (
          <div className="rounded-lg border border-surface-variant bg-surface-container-low px-md py-sm font-body-md text-body-md text-on-surface-variant">
            {notice}
          </div>
        ) : null}
        <div className="grid grid-cols-1 gap-gutter lg:grid-cols-2">
          {managedDocumentTypes.map((documentType) => {
            const typeDocuments = documents.filter((document) => document.documentType === documentType.type);
            const activeDocument = typeDocuments.find((document) => document.isActive);
            return (
              <section className="rounded-lg border border-surface-variant bg-surface-container-lowest p-md" key={documentType.type}>
                <div className="flex items-start justify-between gap-md">
                  <div className="flex min-w-0 items-start gap-sm">
                    <span className="material-symbols-outlined text-surface-tint">{documentType.icon}</span>
                    <div className="min-w-0">
                      <h4 className="font-headline-sm text-headline-sm text-primary">{documentType.title}</h4>
                      <p className="font-body-md text-body-md text-on-surface-variant">{documentType.note}</p>
                    </div>
                  </div>
                  <span
                    className={`rounded-full px-sm py-xs font-label-sm text-label-sm ${
                      activeDocument ? "bg-secondary-container text-on-secondary-container" : "border border-error-container text-on-error-container"
                    }`}
                  >
                    {activeDocument ? "Active" : "Missing"}
                  </span>
                </div>
                <label className="mt-md inline-flex cursor-pointer items-center gap-xs rounded border border-outline-variant bg-surface px-sm py-xs font-label-md text-label-md text-primary hover:bg-surface-container">
                  <span className="material-symbols-outlined text-[16px]">upload</span>
                  {activeDocument ? "Replace" : "Upload"}
                  <input
                    accept={documentType.accept}
                    className="sr-only"
                    disabled={loading}
                    onChange={(event) => {
                      const file = event.currentTarget.files?.[0];
                      if (file) onUpload(documentType.type, file);
                      event.currentTarget.value = "";
                    }}
                    type="file"
                  />
                </label>
                <div className="mt-md space-y-sm">
                  {typeDocuments.length ? (
                    typeDocuments.map((document) => (
                      <div className="rounded border border-surface-variant bg-surface p-sm" key={document.id}>
                        <div className="flex flex-col gap-sm md:flex-row md:items-center md:justify-between">
                          <div className="min-w-0">
                            <div className="truncate font-body-md text-body-md text-primary">{document.originalFilename}</div>
                            <div className="font-label-sm text-label-sm text-on-surface-variant">
                              {document.isActive ? "Active document" : "Inactive"} {formatSize(document.fileSizeBytes)}
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-xs">
                            {!document.isActive ? (
                              <button
                                className="rounded border border-outline-variant bg-surface-container-low px-sm py-xs font-label-md text-label-md text-primary"
                                onClick={() => onActivate(document.id)}
                                type="button"
                              >
                                Activate
                              </button>
                            ) : null}
                            {document.documentType !== "resume_pdf" ? (
                              <button
                                className="rounded border border-outline-variant bg-surface-container-low px-sm py-xs font-label-md text-label-md text-primary"
                                onClick={() => onPreview(document.id)}
                                type="button"
                              >
                                Preview
                              </button>
                            ) : null}
                            <button
                              className="rounded border border-outline-variant bg-surface-container-low px-sm py-xs font-label-md text-label-md text-on-error-container"
                              onClick={() => onDelete(document.id)}
                              type="button"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded border border-dashed border-outline-variant bg-surface px-sm py-md font-body-md text-body-md text-on-surface-variant">
                      No {documentType.title.toLowerCase()} uploaded yet.
                    </div>
                  )}
                </div>
              </section>
            );
          })}
        </div>
        {preview ? (
          <section className="rounded-lg border border-surface-variant bg-surface p-md">
            <div className="mb-sm flex items-center justify-between gap-sm">
              <h4 className="font-headline-sm text-headline-sm text-primary">Markdown Preview</h4>
              {preview.truncated ? <span className="font-label-sm text-label-sm text-on-surface-variant">Truncated</span> : null}
            </div>
            <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded bg-surface-container-low p-md font-body-md text-body-md text-on-surface">
              {preview.content}
            </pre>
          </section>
        ) : null}
      </div>
    </SettingsSection>
  );
}

import type { UserDocument } from "../types";

export default function PrivateProfileFileStatus({ document }: { document: UserDocument }) {
  const connected = document.status === "connected";

  return (
    <div className={`rounded-DEFAULT bg-surface-container-low p-3 ${connected ? "" : "border border-error-container"}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="material-symbols-outlined shrink-0 text-on-surface-variant">
            {document.documentType === "resume_pdf" ? "picture_as_pdf" : "description"}
          </span>
          <div className="min-w-0">
            <div className="truncate font-body-md text-body-md font-medium text-on-surface">{document.storedPath}</div>
            <div className="font-label-sm text-label-sm text-on-surface-variant">
              {document.documentType === "profile_markdown" ? "Profile Summary" : "Resume PDF"}
            </div>
          </div>
        </div>
        <div className={`flex items-center gap-1 ${connected ? "text-primary" : "text-error"}`}>
          <span className="material-symbols-outlined icon-fill text-[16px]">{connected ? "check_circle" : "error"}</span>
          <span className="font-label-sm text-label-sm">{connected ? "Connected" : "Missing"}</span>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="rounded border border-outline-variant bg-surface px-3 py-1.5 font-label-md text-label-md text-primary" type="button">
          Upload
        </button>
        <button className="rounded border border-outline-variant bg-surface px-3 py-1.5 font-label-md text-label-md text-primary" type="button">
          Replace
        </button>
        <button className="rounded border border-outline-variant bg-surface px-3 py-1.5 font-label-md text-label-md text-primary" type="button">
          Preview
        </button>
      </div>
    </div>
  );
}

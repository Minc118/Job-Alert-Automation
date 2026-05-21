export default function MetricCard({
  label,
  value,
  highlight = false,
  accent = false,
  muted = false,
}: {
  label: string;
  value: number;
  highlight?: boolean;
  accent?: boolean;
  muted?: boolean;
}) {
  if (highlight) {
    return (
      <div className="col-span-2 flex h-[100px] flex-col justify-between rounded-xl bg-primary p-4 shadow-ambient md:col-span-1">
        <span className="font-label-md text-label-md text-on-primary opacity-80">{label}</span>
        <div className="flex items-baseline gap-2">
          <span className="font-headline-md text-headline-md text-on-primary">{value}</span>
          <span className="material-symbols-outlined text-[16px] text-on-primary">local_fire_department</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex h-[100px] flex-col justify-between rounded-xl bg-surface-container-lowest p-4 shadow-ambient ${
        accent ? "border-l-4 border-secondary" : ""
      } ${muted ? "opacity-70" : ""}`}
    >
      <span className="font-label-md text-label-md text-on-surface-variant">{label}</span>
      <span className={`font-headline-md text-headline-md ${accent ? "text-secondary" : muted ? "text-outline" : "text-primary"}`}>
        {value}
      </span>
    </div>
  );
}

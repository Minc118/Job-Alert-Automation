export default function RecentActivity({ items: providedItems }: { items?: Array<{ label: string; time: string }> }) {
  const fallbackItems = [
    ["Latest analysis import", "Today, 10:05", true],
    ["Latest job fetch completed", "Today, 09:32", false],
    ["Manual database migration checked", "Today, 09:20", false],
  ] as const;
  const items = providedItems?.length
    ? providedItems.map((item, index) => [item.label, item.time, index === 0] as const)
    : fallbackItems;

  return (
    <section className="rounded-xl bg-surface-container-lowest p-6 shadow-ambient">
      <h3 className="mb-6 font-headline-sm text-headline-sm text-primary">Recent Activity</h3>
      <div className="relative space-y-6 border-l border-surface-variant pl-4">
        {items.map(([title, time, active]) => (
          <div className="relative" key={title}>
            <div
              className={`absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full border-2 border-surface-container-lowest ${
                active ? "bg-primary" : "bg-surface-variant"
              }`}
            />
            <p className="font-body-md text-body-md text-on-surface">{title}</p>
            <p className="mt-1 font-label-sm text-label-sm text-on-surface-variant">{time}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

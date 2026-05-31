export default function SimulationBanner({ subtitle }) {
  return (
    <div className="rounded-lg border-2 border-dashed border-amber-400 bg-amber-50 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center rounded bg-amber-500 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-white">
          Simulation Mode
        </span>
        <span className="text-sm font-semibold text-amber-900">
          No real payments · No production user data · localStorage only
        </span>
      </div>
      {subtitle ? (
        <p className="mt-2 text-sm text-amber-800">{subtitle}</p>
      ) : null}
    </div>
  )
}

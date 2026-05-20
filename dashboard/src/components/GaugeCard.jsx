export default function GaugeCard({ label, value, unit, quality, lastTs, min = 0, max = 100 }) {
  const STALE_MS = 30_000
  const now      = Date.now()
  const isStale  = !lastTs || (now - lastTs) > STALE_MS
  const isGood   = quality === 1 && !isStale && value != null

  let valueColour = 'text-slate-800'
  if (isStale || value == null) {
    valueColour = 'text-slate-400'
  } else {
    const pct = (value - min) / (max - min)
    if (pct >= 0.85)      valueColour = 'text-red-600'
    else if (pct >= 0.65) valueColour = 'text-amber-600'
    else                  valueColour = 'text-emerald-700'
  }

  const displayValue = value != null
    ? (Number.isInteger(value) ? value : value.toFixed(2))
    : '\u2014'

  const relTime = lastTs
    ? (() => {
        const diff = Math.round((now - lastTs) / 1000)
        if (diff < 5)   return 'just now'
        if (diff < 60)  return `${diff}s ago`
        return `${Math.round(diff / 60)}m ago`
      })()
    : 'no data'

  return (
    <div className={`rounded-xl border p-4 transition-opacity ${isStale ? 'opacity-50 border-slate-200 bg-white' : 'border-slate-200 bg-white shadow-sm'}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isGood ? 'bg-emerald-500' : quality === 0 ? 'bg-red-400' : 'bg-slate-300'}`} />
      </div>

      <div className={`text-4xl font-bold tabular-nums leading-none mb-1 ${valueColour}`}>
        {displayValue}
        <span className="text-base font-normal text-slate-400 ml-1">{unit}</span>
      </div>

      <div className="text-xs text-slate-400 mt-2">
        {isStale
          ? <span className="text-amber-500 font-medium">Stale {'\u2014'} {relTime}</span>
          : relTime}
      </div>
    </div>
  )
}

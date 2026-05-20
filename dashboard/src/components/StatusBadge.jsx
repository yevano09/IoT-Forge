export default function StatusBadge({ status = 'unknown', size = 'md' }) {
  const configs = {
    online:  { dot: 'bg-green-500',  text: 'text-green-700',  bg: 'bg-green-50',  border: 'border-green-200',  label: 'Online'  },
    offline: { dot: 'bg-gray-400',   text: 'text-gray-600',   bg: 'bg-gray-50',   border: 'border-gray-200',   label: 'Offline' },
    stale:   { dot: 'bg-amber-400',  text: 'text-amber-700',  bg: 'bg-amber-50',  border: 'border-amber-200',  label: 'Stale'   },
    unknown: { dot: 'bg-slate-300',  text: 'text-slate-500',  bg: 'bg-slate-50',  border: 'border-slate-200',  label: '\u2014'   },
  }
  const c    = configs[status] ?? configs.unknown
  const pad  = size === 'sm' ? 'px-1.5 py-0.5 text-xs' : 'px-2.5 py-1 text-sm'
  const dot  = size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2'

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${pad} ${c.bg} ${c.border} ${c.text}`}>
      <span className={`rounded-full flex-shrink-0 ${dot} ${c.dot}`} />
      {c.label}
    </span>
  )
}

import { useState, useEffect } from 'react'

const GW_API = '/gw'

export default function GatewayPanel() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const fetchHealth = () =>
      fetch(`${GW_API}/health`)
        .then(r => r.ok ? r.json() : null)
        .then(setHealth)
        .catch(() => {})

    fetchHealth()
    const id = setInterval(fetchHealth, 10_000)
    return () => clearInterval(id)
  }, [])

  if (!health) {
    return (
      <div className="px-4 py-3 border-t border-slate-200">
        <p className="text-xs text-slate-400">Gateway connecting...</p>
      </div>
    )
  }

  const upstreamOk = health.upstream_connected

  return (
    <div className="px-4 py-3 border-t border-slate-200">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${upstreamOk ? 'bg-green-500' : 'bg-red-400'}`} />
        <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">RPi Gateway</span>
      </div>
      <div className="text-xs text-slate-500 space-y-1">
        <div className="flex justify-between">
          <span>Upstream</span>
          <span className={`font-medium ${upstreamOk ? 'text-green-600' : 'text-red-500'}`}>
            {upstreamOk ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Devices</span>
          <span className="font-medium text-slate-700">{health.known_devices}</span>
        </div>
        <div className="flex justify-between">
          <span>Forwarded</span>
          <span className="font-medium text-slate-700">{health.forwarded}</span>
        </div>
        <div className="flex justify-between">
          <span>Buffered</span>
          <span className="font-medium text-slate-700">{health.buffered}</span>
        </div>
        <div className="flex justify-between">
          <span>Buffer</span>
          <span className={`font-medium ${health.buffer_size > 0 ? 'text-amber-600' : 'text-slate-500'}`}>
            {health.buffer_size}
          </span>
        </div>
      </div>
    </div>
  )
}

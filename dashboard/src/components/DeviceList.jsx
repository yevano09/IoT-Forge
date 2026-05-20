import { useState } from 'react'
import StatusBadge from './StatusBadge.jsx'

export default function DeviceList({ devices = [], selectedDevice, onSelect, connected }) {
  const [offlineOpen, setOfflineOpen] = useState(false)

  const relTime = (ts) => {
    if (!ts) return '\u2014'
    const diff = Math.round((Date.now() - ts) / 1000)
    if (diff < 5)   return 'just now'
    if (diff < 60)  return `${diff}s ago`
    if (diff < 3600) return `${Math.round(diff/60)}m ago`
    return `${Math.round(diff/3600)}h ago`
  }

  const effectiveStatus = (d) => {
    if (!d.last_seen) return 'unknown'
    const staleSec = (Date.now() - d.last_seen) / 1000
    if (staleSec > 90) return 'offline'
    return d.status || 'online'
  }

  const online = devices.filter(d => effectiveStatus(d) !== 'offline')
  const offline = devices.filter(d => effectiveStatus(d) === 'offline')

  const DeviceButton = ({ d }) => {
    const status   = effectiveStatus(d)
    const selected = selectedDevice === d.device_id
    return (
      <button
        onClick={() => onSelect(d.device_id)}
        className={`w-full flex flex-col gap-1 px-4 py-3 text-left hover:bg-slate-50 transition-colors ${selected ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-medium text-slate-700 truncate max-w-[120px]">
            {d.device_id}
          </span>
          <StatusBadge status={status} size="sm" />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">{relTime(d.last_seen)}</span>
          {d.fw_version && (
            <span className="text-xs text-slate-400 font-mono">{d.fw_version}</span>
          )}
        </div>
      </button>
    )
  }

  return (
    <aside className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
        <h2 className="font-semibold text-slate-700 text-sm">Devices</h2>
        <StatusBadge status={connected ? 'online' : 'offline'} size="sm" />
      </div>

      <button
        onClick={() => onSelect(null)}
        className={`flex items-center gap-2 px-4 py-2.5 text-sm text-left border-b border-slate-100 hover:bg-slate-50 transition-colors ${!selectedDevice ? 'bg-blue-50 text-blue-700 font-medium' : 'text-slate-600'}`}
      >
        <span className="w-2 h-2 rounded-full bg-blue-400 flex-shrink-0" />
        All devices
        <span className="ml-auto text-xs text-slate-400">{devices.length}</span>
      </button>

      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {devices.length === 0 && (
          <div className="px-4 py-6 text-xs text-slate-400 text-center">
            No devices yet.<br />Start the simulator.
          </div>
        )}

        {online.map(d => <DeviceButton key={d.device_id} d={d} />)}
      </div>

      {offline.length > 0 && (
        <div className="border-t border-slate-200">
          <button
            onClick={() => setOfflineOpen(!offlineOpen)}
            className="flex items-center gap-2 w-full px-4 py-2.5 text-xs text-slate-500 hover:bg-slate-50 transition-colors"
          >
            <span className={`transform transition-transform ${offlineOpen ? 'rotate-90' : ''}`}>&#9654;</span>
            Offline
            <span className="ml-auto text-xs text-slate-400">{offline.length}</span>
          </button>
          {offlineOpen && (
            <div className="divide-y divide-slate-100 max-h-48 overflow-y-auto">
              {offline.map(d => <DeviceButton key={d.device_id} d={d} />)}
            </div>
          )}
        </div>
      )}
    </aside>
  )
}

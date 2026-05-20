import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts'

const SENSOR_COLOURS = {
  temperature:    '#ef4444',
  humidity:       '#3b82f6',
  vibration_rms:  '#f97316',
  vibration_peak: '#fb923c',
  motor_current:  '#22c55e',
  default:        '#8b5cf6',
}

const MAX_POINTS = 50

export default function SensorChart({ deviceId, sensor, unit, data = [], height = 200 }) {
  const colour  = SENSOR_COLOURS[sensor] ?? SENSOR_COLOURS.default
  const visible = data.slice(-MAX_POINTS)

  const formatTime = (ts) => {
    const d = new Date(ts)
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
  }

  const formatTooltip = (value) =>
    value != null ? [`${Number(value).toFixed(3)} ${unit}`, sensor] : ['\u2014', sensor]

  if (visible.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-slate-400 text-sm"
        style={{ height }}
      >
        Waiting for data {'\u2014'} {sensor}
      </div>
    )
  }

  const values  = visible.map(d => d.value).filter(v => v != null)
  const yMin    = Math.min(...values)
  const yMax    = Math.max(...values)
  const yPad    = Math.max((yMax - yMin) * 0.1, 0.01)
  const domain  = [+(yMin - yPad).toFixed(3), +(yMax + yPad).toFixed(3)]

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          {deviceId} {'\u2014'} {sensor}
        </span>
        <span className="text-xs text-slate-400">{unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={visible} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="ts"
            tickFormatter={formatTime}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={domain}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickFormatter={v => v.toFixed(2)}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={formatTime}
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={colour}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

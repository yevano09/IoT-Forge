import { useState, useEffect } from 'react'
import DeviceList  from './components/DeviceList.jsx'
import GaugeCard   from './components/GaugeCard.jsx'
import SensorChart from './components/SensorChart.jsx'
import GatewayPanel from './components/GatewayPanel.jsx'
import { useSensorStream } from './hooks/useSensorStream.js'

const API_BASE        = ''
const DEVICE_POLL_MS  = 10_000

const SENSOR_META = {
  temperature:    { label: 'Temperature',   unit: '\u00b0C', min: 0,   max: 80  },
  humidity:       { label: 'Humidity',      unit: '%RH',   min: 0,   max: 100 },
  vibration_rms:  { label: 'Vibration RMS', unit: 'g',     min: 0,   max: 0.5 },
  vibration_peak: { label: 'Vibe Peak',     unit: 'g',     min: 0,   max: 1.0 },
  motor_current:  { label: 'Motor Current', unit: 'A',     min: 0,   max: 20  },
}

export default function App() {
  const [devices,        setDevices]        = useState([])
  const [selectedDevice, setSelectedDevice] = useState(null)

  const { readings, connected } = useSensorStream(API_BASE)

  useEffect(() => {
    const fetchDevices = () =>
      fetch(`${API_BASE}/api/v1/devices`)
        .then(r => r.ok ? r.json() : [])
        .then(setDevices)
        .catch(() => {})

    fetchDevices()
    const id = setInterval(fetchDevices, DEVICE_POLL_MS)
    return () => clearInterval(id)
  }, [])

  const visibleDevices = selectedDevice
    ? [selectedDevice]
    : [...new Set([
        ...devices.map(d => d.device_id),
        ...[...readings.keys()].map(k => k.split('::')[0])
      ])]

  const visibleSensors = [...new Set(
    [...readings.keys()]
      .filter(k => visibleDevices.includes(k.split('::')[0]))
      .map(k => k.split('::')[1])
  )]

  const latestFor = (deviceId, sensor) => {
    const key  = `${deviceId}::${sensor}`
    const buf  = readings.get(key) || []
    return buf[buf.length - 1] ?? null
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">

      <div className="w-56 flex-shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-4 py-4 border-b border-slate-200">
          <h1 className="font-bold text-slate-800 text-base leading-tight">IoT Forge</h1>
          <p className="text-xs text-slate-500 mt-0.5">Edge Sense {'\u00b7'} Month 1</p>
        </div>
        <DeviceList
          devices={devices}
          selectedDevice={selectedDevice}
          onSelect={setSelectedDevice}
          connected={connected}
        />
        <div className="mt-auto">
          <GatewayPanel />
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-12 bg-white border-b border-slate-200 flex items-center px-6 gap-4 flex-shrink-0">
          <h2 className="text-sm font-semibold text-slate-700">
            {selectedDevice ? selectedDevice : 'All devices'}
          </h2>
          {!connected && (
            <span className="text-xs text-amber-600 font-medium bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
              Stream disconnected {'\u2014'} reconnecting{'\u2026'}
            </span>
          )}
          <span className="ml-auto text-xs text-slate-400">
            {readings.size} stream keys {'\u00b7'} {devices.length} devices
          </span>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {visibleSensors.length > 0 && (
            <section className="mb-6">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                Current values {selectedDevice ? `\u00b7 ${selectedDevice}` : '\u00b7 first device'}
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {visibleSensors.map(sensor => {
                  const devId  = selectedDevice ?? visibleDevices[0]
                  const latest = devId ? latestFor(devId, sensor) : null
                  const meta   = SENSOR_META[sensor] ?? { label: sensor, unit: '', min: 0, max: 100 }
                  return (
                    <GaugeCard
                      key={sensor}
                      label={meta.label}
                      value={latest?.value ?? null}
                      unit={meta.unit}
                      quality={latest?.quality ?? 0}
                      lastTs={latest?.ts ?? null}
                      min={meta.min}
                      max={meta.max}
                    />
                  )
                })}
              </div>
            </section>
          )}

          {visibleDevices.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400 text-sm gap-2">
              <span className="text-4xl">{'\ud83d\udce1'}</span>
              <p>No data yet. Start the simulator:</p>
              <code className="text-xs bg-slate-100 px-3 py-1.5 rounded font-mono">
                python simulator.py --devices 3 --interval 2 --anomaly
              </code>
            </div>
          )}

          {visibleDevices.map(deviceId =>
            visibleSensors.map(sensor => {
              const key  = `${deviceId}::${sensor}`
              const data = readings.get(key) || []
              if (data.length === 0) return null
              const meta = SENSOR_META[sensor] ?? { label: sensor, unit: '' }
              return (
                <div key={key} className="mb-4">
                  <SensorChart
                    deviceId={deviceId}
                    sensor={sensor}
                    unit={meta.unit}
                    data={data}
                    height={180}
                  />
                </div>
              )
            })
          )}
        </main>
      </div>
    </div>
  )
}

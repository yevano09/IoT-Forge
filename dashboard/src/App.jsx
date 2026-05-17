import React from 'react';
import { useSensorStream } from './hooks/useSensorStream';
import { StatusBadge } from './components/StatusBadge';
import { GaugeCard } from './components/GaugeCard';
import { SensorChart } from './components/SensorChart';
import { DeviceList } from './components/DeviceList';

function App() {
  const {
    devices,
    selectedDevice,
    setSelectedDevice,
    latestReadings,
    readingsHistory,
    connected
  } = useSensorStream();

  const selectedDeviceData = devices.find(d => d.device_id === selectedDevice);

  const sensorsForDevice = Object.keys(latestReadings)
    .filter(key => key.startsWith(selectedDevice || ''))
    .map(key => {
      const reading = latestReadings[key];
      return {
        key,
        sensor: reading.sensor,
        value: reading.value,
        unit: reading.unit,
        ts: reading.ts
      };
    });

  const uniqueSensors = [...new Set(sensorsForDevice.map(s => s.sensor))];

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">IoT Forge Dashboard</h1>
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <DeviceList
              devices={devices}
              selectedDevice={selectedDevice}
              onSelect={setSelectedDevice}
            />
          </div>

          <div className="lg:col-span-3 space-y-6">
            {selectedDevice && selectedDeviceData && (
              <div className="bg-white p-4 rounded-lg border border-gray-300">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-800">{selectedDevice}</h2>
                  <StatusBadge
                    status={selectedDeviceData.status}
                    lastSeen={selectedDeviceData.last_seen}
                  />
                </div>
                {selectedDeviceData.rssi && (
                  <div className="text-sm text-gray-500">
                    RSSI: {selectedDeviceData.rssi} dBm | Uptime: {selectedDeviceData.uptime_s}s
                  </div>
                )}
              </div>
            )}

            {uniqueSensors.length > 0 && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {uniqueSensors.map(sensor => {
                    const reading = sensorsForDevice.find(s => s.sensor === sensor);
                    return (
                      <GaugeCard
                        key={sensor}
                        sensor={sensor}
                        value={reading?.value}
                        unit={reading?.unit}
                        timestamp={reading?.ts}
                      />
                    );
                  })}
                </div>

                <div className="space-y-4">
                  {uniqueSensors.map(sensor => {
                    const key = `${selectedDevice}-${sensor}`;
                    const history = readingsHistory[key] || [];
                    const reading = sensorsForDevice.find(s => s.sensor === sensor);
                    return (
                      <SensorChart
                        key={sensor}
                        readings={history}
                        sensor={sensor}
                        unit={reading?.unit || ''}
                      />
                    );
                  })}
                </div>
              </>
            )}

            {!selectedDevice && (
              <div className="text-center text-gray-400 py-12">
                Select a device to view sensor data
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
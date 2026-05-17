import React from 'react';
import { StatusBadge } from './StatusBadge';

export function DeviceList({ devices, selectedDevice, onSelect }) {
  if (!devices || devices.length === 0) {
    return (
      <div className="p-4 text-gray-400 text-center">No devices found</div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-500 mb-3">Devices</h3>
      {devices.map(device => (
        <button
          key={device.device_id}
          onClick={() => onSelect(device.device_id)}
          className={`w-full p-3 rounded-lg border text-left transition-colors ${
            selectedDevice === device.device_id
              ? 'bg-blue-50 border-blue-500'
              : 'bg-white border-gray-200 hover:bg-gray-50'
          }`}
        >
          <div className="flex justify-between items-center">
            <span className="font-medium text-gray-800 text-sm">
              {device.device_id}
            </span>
            <StatusBadge
              status={device.status}
              lastSeen={device.last_seen}
            />
          </div>
          {device.fw_version && (
            <div className="text-xs text-gray-400 mt-1">
              v{device.fw_version}
            </div>
          )}
        </button>
      ))}
    </div>
  );
}
import React from 'react';

export function GaugeCard({ sensor, value, unit, timestamp }) {
  const now = Date.now();
  const isStale = timestamp && (now - timestamp) > 30000;
  const isGrayed = isStale;

  return (
    <div className={`p-4 rounded-lg border ${isGrayed ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-300'}`}>
      <div className="text-sm font-medium text-gray-500 mb-1 capitalize">
        {sensor.replace(/_/g, ' ')}
      </div>
      <div className={`text-3xl font-bold ${isGrayed ? 'text-gray-400' : 'text-gray-900'}`}>
        {value !== undefined ? value.toFixed(2) : '--'}
        <span className="text-lg font-normal text-gray-500 ml-1">{unit}</span>
      </div>
      {isStale && (
        <div className="text-xs text-yellow-600 mt-1">Data stale</div>
      )}
    </div>
  );
}
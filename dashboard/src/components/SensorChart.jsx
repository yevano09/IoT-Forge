import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function SensorChart({ readings, sensor, unit }) {
  const chartData = (readings || []).slice(-50).map(r => ({
    time: new Date(r.ts).toLocaleTimeString(),
    value: r.value
  }));

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-400">
        No data available
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-300">
      <h3 className="text-sm font-medium text-gray-500 mb-2 capitalize">
        {sensor.replace(/_/g, ' ')} ({unit})
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <YAxis
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '4px'
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
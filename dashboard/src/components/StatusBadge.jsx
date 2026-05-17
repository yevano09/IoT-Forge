import React from 'react';

export function StatusBadge({ status, lastSeen }) {
  let dotColor = 'bg-gray-400';
  let label = 'Unknown';

  const now = Date.now();
  const isStale = lastSeen && (now - lastSeen) > 60000;

  if (status === 'online' && !isStale) {
    dotColor = 'bg-green-500';
    label = 'Online';
  } else if (status === 'online' && isStale) {
    dotColor = 'bg-yellow-500';
    label = 'Stale';
  } else {
    dotColor = 'bg-red-500';
    label = 'Offline';
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
      <span className="text-gray-600">{label}</span>
    </span>
  );
}
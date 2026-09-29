import React from 'react';

export default function CapacityBar({ requiredBytes, capacityBytes, utilizationPct }) {
  const isOver = requiredBytes > capacityBytes;
  const clampedPct = Math.min(100, Math.max(0, utilizationPct || 0));

  const formatBytes = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-slate-50/90 border border-slate-200/80 rounded-2xl p-4">
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="text-slate-700 font-bold">Carrier Headroom</span>
        <span
          className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold ${
            isOver
              ? 'bg-cubist-crimson/15 text-cubist-crimson border border-cubist-crimson/30'
              : 'bg-cubist-green/15 text-cubist-green border border-cubist-green/30'
          }`}
        >
          {isOver ? 'Exceeds capacity' : 'Fits comfortably'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden p-[1px]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isOver
              ? 'bg-cubist-crimson'
              : clampedPct > 80
              ? 'bg-cubist-ochre'
              : 'bg-gradient-to-r from-cubist-blue to-cubist-green'
          }`}
          style={{ width: `${isOver ? 100 : clampedPct}%` }}
        ></div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
        <div className="bg-white rounded-lg p-2 border border-slate-200/80 shadow-2xs">
          <span className="text-slate-400 block text-[9px] uppercase font-mono">Payload</span>
          <span className="font-semibold text-slate-800 font-mono">
            {formatBytes(requiredBytes)}
          </span>
        </div>
        <div className="bg-white rounded-lg p-2 border border-slate-200/80 shadow-2xs">
          <span className="text-slate-400 block text-[9px] uppercase font-mono">Capacity</span>
          <span className="font-semibold text-slate-800 font-mono">
            {formatBytes(capacityBytes)}
          </span>
        </div>
        <div className="bg-white rounded-lg p-2 border border-slate-200/80 shadow-2xs">
          <span className="text-slate-400 block text-[9px] uppercase font-mono">Used</span>
          <span
            className={`font-semibold font-mono ${
              isOver ? 'text-cubist-crimson' : 'text-slate-800'
            }`}
          >
            {utilizationPct ? `${utilizationPct.toFixed(1)}%` : '0%'}
          </span>
        </div>
      </div>
    </div>
  );
}

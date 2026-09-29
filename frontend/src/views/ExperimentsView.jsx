import React, { useState, useEffect } from 'react';
import { Filter, FlaskConical, BarChart3, Clock, Layers } from 'lucide-react';

export default function ExperimentsView() {
  const [data, setData] = useState([]);
  const [plots, setPlots] = useState([]);

  // Filters
  const [selectedRes, setSelectedRes] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedMode, setSelectedMode] = useState('ALL');

  useEffect(() => {
    fetch('http://localhost:8000/api/experiments')
      .then((res) => res.json())
      .then((json) => {
        setData(json.results || []);
        setPlots(json.plots || []);
      })
      .catch((err) => console.error('Failed to load experiments:', err));
  }, []);

  const filteredData = data.filter((item) => {
    if (selectedRes !== 'ALL' && item.resolution !== selectedRes) return false;
    if (selectedType !== 'ALL' && item.payload_type !== selectedType) return false;
    if (selectedMode !== 'ALL' && item.mode !== selectedMode) return false;
    return true;
  });

  return (
    <div className="relative w-full max-w-5xl">
      {/* Editorial Header */}
      <div className="mb-6 pt-2">
        <h1 className="text-4xl sm:text-5xl font-display font-extrabold text-ink-950 tracking-tight leading-[1.08]">
          Performance <span className="text-cubist-blue">Benchmarks</span>
        </h1>
        <div className="flex items-center gap-3.5 mt-3.5">
          <div className="w-8 h-[1.5px] bg-ink-950"></div>
          <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-slate-500">
            12 EMPIRICAL SCENARIOS • CONTROLLED RUNS • TELEMETRY
          </p>
        </div>
      </div>

      {/* Floating White Main Workspace Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-editorial border border-slate-200/80 space-y-6">
        
        {/* Filter Bar */}
        <div className="bg-slate-50/90 rounded-2xl p-4 sm:p-5 border border-slate-200/70 flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-700 font-bold">
            <Filter className="w-4 h-4 text-cubist-blue" />
            <span className="uppercase tracking-wider text-[11px] font-mono">Filters:</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">Resolution</span>
            <select
              value={selectedRes}
              onChange={(e) => setSelectedRes(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-ink-950 focus:outline-none focus:border-cubist-blue font-mono shadow-2xs"
            >
              <option value="ALL">All (250px & 500px)</option>
              <option value="250x250">250×250</option>
              <option value="500x500">500×500</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">Type</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-ink-950 focus:outline-none focus:border-cubist-blue font-mono shadow-2xs"
            >
              <option value="ALL">All Types (PDF, TXT, BIN)</option>
              <option value="PDF">PDF (~500 B)</option>
              <option value="TXT">TXT (~3 KB)</option>
              <option value="BIN">BIN (~15 KB)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">Mode</span>
            <select
              value={selectedMode}
              onChange={(e) => setSelectedMode(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-ink-950 focus:outline-none focus:border-cubist-blue font-mono shadow-2xs"
            >
              <option value="ALL">All Configurations</option>
              <option value="Plain LSB">Direct LSB</option>
              <option value="zlib + AES-GCM">Compressed & Encrypted</option>
            </select>
          </div>

          <span className="ml-auto font-mono text-slate-500 text-[11px]">
            Showing {filteredData.length} of {data.length} records
          </span>
        </div>

        {/* Benchmark Visualizations Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Analytical Evaluation Curves
            </span>
            <span className="text-xs font-mono text-slate-500">
              Generated Matplotlib Benchmarks
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {plots.map((plot) => (
              <div
                key={plot.id}
                className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col items-center hover:border-slate-300 transition-colors"
              >
                <div className="w-full flex items-center justify-between mb-3 px-1">
                  <span className="text-xs font-bold text-ink-950">
                    {plot.title}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400 uppercase">Analysis</span>
                </div>
                <img
                  src={`http://localhost:8000${plot.url}`}
                  alt={plot.title}
                  className="w-full rounded-xl border border-slate-200 bg-white shadow-2xs object-contain"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Dataset Table */}
        <div className="space-y-4 pt-4 border-t border-slate-100 overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Benchmark Dataset Table
            </span>
            <span className="text-xs font-mono text-slate-500">
              Controlled Scenario Logs
            </span>
          </div>

          <div className="overflow-x-auto rounded-2xl border border-slate-200/80">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-3.5">Run</th>
                  <th className="py-3 px-3.5">Resolution</th>
                  <th className="py-3 px-3.5">Payload</th>
                  <th className="py-3 px-3.5">Size</th>
                  <th className="py-3 px-3.5">Mode</th>
                  <th className="py-3 px-3.5">Used %</th>
                  <th className="py-3 px-3.5">MSE</th>
                  <th className="py-3 px-3.5 text-cubist-blue font-bold">PSNR</th>
                  <th className="py-3 px-3.5 text-cubist-green font-bold">SSIM</th>
                  <th className="py-3 px-3.5">Encode</th>
                  <th className="py-3 px-3.5">Decode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filteredData.map((row) => (
                  <tr key={row.exp_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3.5 text-slate-400">#{row.exp_id}</td>
                    <td className="py-2.5 px-3.5 text-ink-950 font-bold">{row.resolution}</td>
                    <td className="py-2.5 px-3.5 text-slate-600">{row.payload_type}</td>
                    <td className="py-2.5 px-3.5 text-ink-950">{row.payload_size_bytes} B</td>
                    <td className="py-2.5 px-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] ${
                          row.mode === 'Plain LSB'
                            ? 'bg-slate-100 text-slate-700 border border-slate-200'
                            : 'bg-cubist-ochre/15 text-cubist-ochre border border-cubist-ochre/30'
                        }`}
                      >
                        {row.mode === 'Plain LSB' ? 'Direct LSB' : 'zlib + AES'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3.5 text-slate-600">{row.utilization_pct}%</td>
                    <td className="py-2.5 px-3.5 text-slate-500">{row.mse.toFixed(5)}</td>
                    <td className="py-2.5 px-3.5 text-cubist-blue font-bold">{row.psnr_db} dB</td>
                    <td className="py-2.5 px-3.5 text-cubist-green font-bold">{row.ssim.toFixed(5)}</td>
                    <td className="py-2.5 px-3.5 text-slate-600">{row.encode_time_ms} ms</td>
                    <td className="py-2.5 px-3.5 text-slate-600">{row.decode_time_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

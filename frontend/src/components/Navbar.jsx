import React from 'react';
import { Home, Eye, BarChart2, FlaskConical } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'encode', label: 'Encode', icon: Home },
    { id: 'decode', label: 'Decode', icon: Eye },
    { id: 'analyze', label: 'Analyze', icon: BarChart2 },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical },
  ];

  return (
    <aside className="w-full lg:w-[17%] lg:min-w-[200px] lg:max-w-[240px] shrink-0 bg-[#090D15] border-b lg:border-b-0 lg:border-r border-[#141B2B] flex flex-col justify-between py-7 px-5 z-40 select-none">
      <div className="space-y-9">
        {/* Brand Logo & Title */}
        <div 
          onClick={() => setActiveTab('encode')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          {/* Authentic PixelVeil Avatar Icon */}
          <div className="w-7 h-14 overflow-hidden shrink-0 shadow-md">
            <img 
              src="/pixelveil-avatar.png" 
              alt="PixelVeil" 
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <span className="font-display font-bold text-white text-xl tracking-tight block leading-none">
              PixelVeil
            </span>
            <span className="text-[8px] font-mono tracking-widest uppercase text-slate-400 block mt-1.5 leading-snug">
              INVISIBLE<br />DATA<br />IN IMAGES
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex flex-row lg:flex-col gap-2 overflow-x-auto lg:overflow-visible">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-3.5 px-4 py-3 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 shrink-0 ${
                  isActive
                    ? 'text-white bg-[#131B2C] shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#0F1624]'
                }`}
              >
                {/* Active Left Accent Pill */}
                {isActive && (
                  <span className="absolute left-0 top-2.5 bottom-2.5 w-1 bg-cubist-blue rounded-r-full"></span>
                )}
                <Icon className={`w-4 h-4 shrink-0 transition-colors ${isActive ? 'text-cubist-blue' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Sidebar Footer details */}
      <div className="hidden lg:block pt-6 border-t border-[#131B2C]">
        <div className="w-5 h-[1.5px] bg-slate-600 mb-3"></div>
        <p className="text-[9px] font-mono tracking-widest uppercase text-slate-400 leading-relaxed">
          SAME<br />
          IMAGE.<br />
          MORE<br />
          POSSIBILITIES.
        </p>
      </div>
    </aside>
  );
}


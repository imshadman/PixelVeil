import React, { useState } from 'react';
import Navbar from './components/Navbar';
import EncodeView from './views/EncodeView';
import DecodeView from './views/DecodeView';
import AnalyzeView from './views/AnalyzeView';
import ExperimentsView from './views/ExperimentsView';

export default function App() {
  const [activeTab, setActiveTab] = useState('encode');

  return (
    <div className="min-h-screen bg-subtle-linen flex flex-col lg:flex-row font-sans selection:bg-cubist-blue/20 selection:text-ink-950">
      {/* Left Vertical Dark Sidebar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden min-h-screen bg-[#F5F1E8]">
        {/* Top Minimal Bar */}
        <div className="w-full flex items-center justify-between px-6 sm:px-10 lg:px-12 pt-5 pb-1 z-30">
          <div className="text-[10px] font-mono tracking-widest text-slate-500 uppercase">
            {/* Kept minimal, heading eyebrow rendered in view */}
          </div>
          
          {/* Subtle minimal theme toggle pill (matches IVPdemo2.png top right) */}
          <button 
            type="button"
            className="w-10 h-5 rounded-full bg-[#0E131F] border border-slate-700/60 p-0.5 flex items-center justify-end shadow-xs cursor-pointer hover:border-slate-500 transition-colors"
            title="Toggle theme"
          >
            <span className="w-3.5 h-3.5 rounded-full bg-white shadow-xs"></span>
          </button>
        </div>

        {/* Content View with authentic composition */}
        <main className="flex-1 px-4 sm:px-8 lg:px-12 py-2 sm:py-3 max-w-6xl w-full mx-auto relative z-10">
          {activeTab === 'encode' && <EncodeView setActiveTab={setActiveTab} />}
          {activeTab === 'decode' && <DecodeView />}
          {activeTab === 'analyze' && <AnalyzeView />}
          {activeTab === 'experiments' && <ExperimentsView />}
        </main>

        {/* Bottom Circular Artwork (Overlaps bottom-left of canvas behind card like in IVPdemo2.png) */}
        <div className="absolute left-[-20px] bottom-0 w-[450px] h-[65px] pointer-events-none select-none z-0 hidden lg:block opacity-95">
          <img 
            src="/cubist-bottom-art.png" 
            alt="Bottom geometric curve" 
            className="w-full h-full object-cover object-left-bottom"
          />
        </div>

        {/* Minimal Bottom Margin Annotation (Matches IVPdemo2.png) */}
        <div className="px-6 sm:px-12 py-3 flex items-center justify-end text-[10px] font-mono text-slate-400 select-none z-10">
          <span>v1.0.0</span>
        </div>
      </div>
    </div>
  );
}


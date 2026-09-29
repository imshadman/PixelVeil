import React, { useState, useRef } from 'react';
import { ArrowRight, Loader2, AlertCircle, BarChart2, Image as ImageIcon } from 'lucide-react';

export default function AnalyzeView() {
  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);
  const coverInputRef = useRef(null);

  const [stegoFile, setStegoFile] = useState(null);
  const [stegoPreview, setStegoPreview] = useState(null);
  const stegoInputRef = useRef(null);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [metricsResult, setMetricsResult] = useState(null);

  const handleCoverSelect = (f) => {
    setCoverFile(f);
    setCoverPreview(URL.createObjectURL(f));
    setMetricsResult(null);
  };

  const handleStegoSelect = (f) => {
    setStegoFile(f);
    setStegoPreview(URL.createObjectURL(f));
    setMetricsResult(null);
  };

  const handleAnalyze = async () => {
    if (!coverFile || !stegoFile) return;

    setIsAnalyzing(true);
    setErrorMsg(null);
    setMetricsResult(null);

    const formData = new FormData();
    formData.append('cover', coverFile);
    formData.append('stego', stegoFile);

    try {
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Quality analysis failed.');
      }

      const data = await res.json();
      setMetricsResult(data);
    } catch (err) {
      setErrorMsg(err.message || 'An error occurred during image comparison.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="relative w-full max-w-4xl">
      {/* Editorial Header */}
      <div className="mb-6 pt-2">
        <h1 className="text-4xl sm:text-5xl font-display font-extrabold text-ink-950 tracking-tight leading-[1.08]">
          Image <span className="text-cubist-blue">Quality</span><br />
          Analysis
        </h1>
        <div className="flex items-center gap-3.5 mt-3.5">
          <div className="w-8 h-[1.5px] bg-ink-950"></div>
          <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-slate-500">
            MATHEMATICAL FIDELITY • MSE • PSNR • SSIM
          </p>
        </div>
      </div>

      {errorMsg && (
        <div className="mb-6 flex items-start gap-3 p-4 rounded-2xl bg-cubist-crimson/10 border border-cubist-crimson/30 text-ink-900 text-xs sm:text-sm shadow-sm">
          <AlertCircle className="w-5 h-5 text-cubist-crimson shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block text-cubist-crimson">Notice</span>
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* Floating White Main Workspace Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-editorial border border-slate-200/80 space-y-6">
        
        {/* Dual Upload Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Cover Input */}
          <input
            type="file"
            ref={coverInputRef}
            accept=".png"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) handleCoverSelect(e.target.files[0]);
            }}
            className="hidden"
          />
          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/70 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3.5 min-w-0">
              <div 
                onClick={() => coverInputRef.current?.click()}
                className="w-16 h-16 rounded-xl overflow-hidden shrink-0 border border-slate-200 bg-white flex items-center justify-center cursor-pointer shadow-sm group"
              >
                {coverPreview ? (
                  <img src={coverPreview} alt="Cover Preview" className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="w-6 h-6 text-slate-400 group-hover:text-cubist-blue" />
                )}
              </div>
              <div className="min-w-0">
                <span className="text-sm font-bold text-ink-950 block">Original Cover PNG</span>
                <span className="text-xs text-slate-500 font-mono block truncate mt-0.5">
                  {coverFile ? coverFile.name : 'Unmodified carrier'}
                </span>
                <button
                  type="button"
                  onClick={() => coverInputRef.current?.click()}
                  className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs"
                >
                  <span>{coverFile ? 'Change' : 'Choose PNG'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Stego Input */}
          <input
            type="file"
            ref={stegoInputRef}
            accept=".png"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) handleStegoSelect(e.target.files[0]);
            }}
            className="hidden"
          />
          <div className="bg-slate-50/90 rounded-2xl p-4 border border-slate-200/70 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3.5 min-w-0">
              <div 
                onClick={() => stegoInputRef.current?.click()}
                className="w-16 h-16 rounded-xl overflow-hidden shrink-0 border border-slate-200 bg-white flex items-center justify-center cursor-pointer shadow-sm group"
              >
                {stegoPreview ? (
                  <img src={stegoPreview} alt="Stego Preview" className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="w-6 h-6 text-slate-400 group-hover:text-cubist-blue" />
                )}
              </div>
              <div className="min-w-0">
                <span className="text-sm font-bold text-ink-950 block">Modified Stego PNG</span>
                <span className="text-xs text-slate-500 font-mono block truncate mt-0.5">
                  {stegoFile ? stegoFile.name : 'Carrier with hidden data'}
                </span>
                <button
                  type="button"
                  onClick={() => stegoInputRef.current?.click()}
                  className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs"
                >
                  <span>{stegoFile ? 'Change' : 'Choose PNG'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Compute CTA */}
        <button
          type="button"
          disabled={!coverFile || !stegoFile || isAnalyzing}
          onClick={handleAnalyze}
          className={`w-full py-4 rounded-full font-display font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-lg transition-all duration-200 ${
            !coverFile || !stegoFile
              ? 'bg-ink-900 text-slate-500 cursor-not-allowed'
              : isAnalyzing
              ? 'bg-ink-950 text-white cursor-wait opacity-90'
              : 'bg-ink-950 hover:bg-black text-white hover:shadow-xl active:scale-[0.99]'
          }`}
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span>Computing quality metrics...</span>
            </>
          ) : (
            <>
              <span>Compute Quality Metrics</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Visual Comparison & Results */}
      {metricsResult && (
        <div className="mt-8 space-y-6 animate-fadeIn">
          {/* Side by Side Panel */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-editorial border border-slate-200/80">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-6">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Side-by-Side Visual Comparison
              </span>
              <span className="text-xs font-mono text-slate-500">
                {metricsResult.width} × {metricsResult.height} px
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col items-center bg-slate-50 rounded-2xl p-4 border border-slate-200/70">
                <span className="text-xs font-mono font-bold text-slate-700 mb-3">
                  Original Cover
                </span>
                <img
                  src={coverPreview}
                  alt="Cover"
                  className="max-h-72 object-contain rounded-xl border border-slate-200 shadow-sm"
                />
              </div>

              <div className="flex flex-col items-center bg-slate-50 rounded-2xl p-4 border border-slate-200/70">
                <span className="text-xs font-mono font-bold text-cubist-blue mb-3">
                  Stego Image (Modified LSBs)
                </span>
                <img
                  src={stegoPreview}
                  alt="Stego"
                  className="max-h-72 object-contain rounded-xl border border-slate-200 shadow-sm"
                />
              </div>
            </div>
            <p className="text-center text-xs text-slate-500 mt-5">
              Notice: The 1-LSB spatial pixel modifications are mathematically isolated and imperceptible to human vision.
            </p>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div className="bg-white border border-slate-200/80 rounded-3xl p-6 text-center shadow-editorial space-y-1">
              <span className="text-xs font-mono uppercase text-slate-400 block">
                Mean Squared Error (MSE)
              </span>
              <div className="text-3xl font-bold font-mono text-ink-950 py-1">
                {metricsResult.mse.toFixed(6)}
              </div>
              <span className="text-[11px] text-slate-500 block">
                Target: Close to 0.0
              </span>
            </div>

            <div className="bg-white border border-cubist-blue/30 rounded-3xl p-6 text-center shadow-editorial space-y-1">
              <span className="text-xs font-mono uppercase text-cubist-blue font-bold block">
                Peak Signal-to-Noise (PSNR)
              </span>
              <div className="text-3xl font-bold font-mono text-cubist-blue py-1">
                {metricsResult.is_infinite_psnr ? '∞ dB' : `${metricsResult.psnr_db.toFixed(2)} dB`}
              </div>
              <span className="text-[11px] text-cubist-green font-bold block">
                &gt; 50 dB Imperceptible
              </span>
            </div>

            <div className="bg-white border border-cubist-green/30 rounded-3xl p-6 text-center shadow-editorial space-y-1">
              <span className="text-xs font-mono uppercase text-cubist-green font-bold block">
                Structural Similarity (SSIM)
              </span>
              <div className="text-3xl font-bold font-mono text-cubist-green py-1">
                {metricsResult.ssim.toFixed(6)}
              </div>
              <span className="text-[11px] text-slate-500 block">
                Scale: 1.0 = Identical
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


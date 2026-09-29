import React, { useState, useEffect, useRef } from 'react';
import CapacityBar from '../components/CapacityBar';
import { 
  Upload, 
  Download, 
  ArrowRight, 
  Loader2, 
  AlertCircle, 
  CheckCircle2, 
  Check, 
  KeyRound, 
  Eye, 
  Sliders, 
  FileText, 
  Image as ImageIcon 
} from 'lucide-react';

export default function EncodeView({ setActiveTab }) {
  const [activeSubTab, setActiveSubTab] = useState('embed'); // 'embed' | 'extract'

  // Cover image state
  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState(null);
  const [coverInfo, setCoverInfo] = useState(null);
  const coverInputRef = useRef(null);

  // Payload file state
  const [payloadFile, setPayloadFile] = useState(null);
  const [headroom, setHeadroom] = useState(null);
  const payloadInputRef = useRef(null);

  // Security & options toggles
  const [compress, setCompress] = useState(true);
  const [encrypt, setEncrypt] = useState(true);
  const [password, setPassword] = useState('••••••••');
  const [showPassword, setShowPassword] = useState(false);

  // Submission & results
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  // Inspect cover when selected
  useEffect(() => {
    if (!coverFile) {
      setCoverInfo(null);
      setCoverPreview(null);
      return;
    }
    const url = URL.createObjectURL(coverFile);
    setCoverPreview(url);
    setErrorMsg(null);
    setResultData(null);

    const formData = new FormData();
    formData.append('cover', coverFile);

    fetch('http://localhost:8000/api/inspect-cover', {
      method: 'POST',
      body: formData,
    })
      .then((res) => {
        if (!res.ok) return res.json().then((d) => Promise.reject(d.detail));
        return res.json();
      })
      .then((data) => setCoverInfo(data))
      .catch((err) => {
        setErrorMsg(typeof err === 'string' ? err : 'Failed to inspect cover image.');
        setCoverFile(null);
      });

    return () => URL.revokeObjectURL(url);
  }, [coverFile]);

  // Check headroom when both cover and payload are present
  useEffect(() => {
    if (!coverFile || !payloadFile) {
      setHeadroom(null);
      return;
    }

    const formData = new FormData();
    formData.append('cover', coverFile);
    formData.append('payload', payloadFile);

    fetch('http://localhost:8000/api/check-headroom', {
      method: 'POST',
      body: formData,
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setHeadroom(data))
      .catch(() => setHeadroom(null));
  }, [coverFile, payloadFile]);

  const handleEncode = async () => {
    if (!coverFile || !payloadFile) {
      setErrorMsg('Please select both a Cover Image and a File to Hide.');
      return;
    }
    if (encrypt && (!password.trim() || password === '••••••••')) {
      setErrorMsg('Please enter your secret password for encryption.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    setResultData(null);

    const formData = new FormData();
    formData.append('cover', coverFile);
    formData.append('payload', payloadFile);
    formData.append('compress', compress ? 'true' : 'false');
    if (encrypt && password) {
      formData.append('password', password);
    }

    const startTime = performance.now();

    try {
      const res = await fetch('http://localhost:8000/api/encode', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Encoding failed.');
      }

      // Extract telemetry from custom headers
      const filename = res.headers.get('X-Payload-Filename') || payloadFile.name;
      const originalSize = res.headers.get('X-Original-Size');
      const embeddedSize = res.headers.get('X-Embedded-Size');
      const headerSize = res.headers.get('X-Header-Size');
      const sha256 = res.headers.get('X-Original-SHA256');
      const encodeTime = res.headers.get('X-Encoding-Time-Sec');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);

      setResultData({
        filename,
        originalSize: Number(originalSize),
        embeddedSize: Number(embeddedSize),
        headerSize: Number(headerSize),
        sha256,
        encodeTimeMs: encodeTime ? (Number(encodeTime) * 1000).toFixed(1) : ((performance.now() - startTime)).toFixed(1),
        isCompressed: compress,
        isEncrypted: encrypt,
      });
    } catch (err) {
      setErrorMsg(err.message || 'An unexpected error occurred during encoding.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes && bytes !== 0) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="relative w-full">
      {/* 
        HERO + LARGE CUBIST ARTWORK COMPOSITION (Matches IVPdemo2.png)
        The cubist artwork is a large compositional background layer behind the hero and card
      */}
      <div className="relative w-full min-h-[200px] flex items-start justify-between mb-1">
        
        {/* LARGE CUBIST ARTWORK BACKDROP LAYER (Layer 1: Behind Hero and Main Card) */}
        <div className="absolute right-[-10px] lg:right-[15px] top-[-75px] sm:top-[-85px] w-[560px] sm:w-[640px] lg:w-[700px] h-[580px] pointer-events-none select-none z-0 hidden md:block overflow-visible">
          <img
            src="/artwork-clean.png"
            alt="Cubist composition"
            className="w-full h-full object-contain object-top-right filter drop-shadow-none"
          />
        </div>

        {/* Left Side: Editorial Typography (Layer 2: Above Artwork) */}
        <div className="relative z-10 pt-0.5 sm:pt-1 max-w-lg">
          <div className="text-[10px] font-mono tracking-widest text-slate-500 uppercase mb-3">
            ORDINARY IMAGES.<br />EXTRAORDINARY SECRETS.
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display font-extrabold text-ink-950 tracking-tight leading-[1.03]">
            Hide<br />
            What <span className="text-cubist-blue">M</span><span className="text-cubist-ochre">at</span><span className="text-cubist-yellow">te</span><span className="text-cubist-ochre">rs</span>
          </h1>

          {/* Subtitle with horizontal rule */}
          <div className="flex items-center gap-3.5 mt-5">
            <div className="w-8 h-[1.5px] bg-ink-950"></div>
            <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-slate-500">
              PRIVATE • SIMPLE • YOURS
            </p>
          </div>
        </div>

        {/* Far Right Vertical Editorial Text (Matches IVPdemo2.png) */}
        <div className="hidden xl:block absolute right-[-28px] top-24 text-right select-none z-10">
          <div className="text-[9px] font-mono tracking-[0.25em] text-slate-400 uppercase leading-[2.2] space-y-1 font-medium">
            <div>HIDE</div>
            <div>CREATE</div>
            <div>EXPLORE</div>
            <div>REVEAL</div>
          </div>
          <div className="w-5 h-[1px] bg-slate-300 ml-auto mt-3"></div>
        </div>
      </div>

      {/* Error notification if any */}
      {errorMsg && (
        <div className="mb-4 flex items-start gap-3 p-4 rounded-2xl bg-cubist-crimson/10 border border-cubist-crimson/30 text-ink-900 text-xs sm:text-sm shadow-xs relative z-20">
          <AlertCircle className="w-5 h-5 text-cubist-crimson shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block text-cubist-crimson">Notice</span>
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* 
        FLOATING WHITE MAIN WORKSPACE CARD (Matches IVPdemo2.png)
        Large white rounded rectangle floating over the cream background and overlapping the artwork
      */}
      <div className="bg-white rounded-[2rem] p-5 sm:p-6 shadow-editorial border border-slate-200/80 relative z-10">
        
        {/* Top Sub-Nav Bar (Embed / Extract + RGB PNG Pill) */}
        <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 mb-4">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => setActiveSubTab('embed')}
              className={`flex items-center gap-2 text-sm font-semibold transition-all relative pb-2.5 ${
                activeSubTab === 'embed'
                  ? 'text-ink-950'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              <Upload className="w-4 h-4 text-cubist-blue" />
              <span>Embed</span>
              {activeSubTab === 'embed' && (
                <span className="absolute bottom-[-1px] left-0 right-0 h-[2.5px] bg-cubist-blue rounded-full"></span>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                if (setActiveTab) setActiveTab('decode');
              }}
              className="flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-slate-700 transition-colors pb-2.5"
            >
              <Download className="w-4 h-4 text-slate-400" />
              <span>Extract</span>
            </button>
          </div>

          {/* RGB PNG Subtle Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100/90 border border-slate-200 text-[11px] font-mono text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full bg-gradient-to-tr from-cubist-crimson via-cubist-ochre to-cubist-blue inline-block"></span>
            <span className="font-semibold">RGB PNG</span>
          </div>
        </div>

        {/* Dual Input Panels (Cover Image & File to Hide) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-5 mb-5">
            
            {/* 1. Cover Image Panel */}
            <div className="bg-slate-50/80 rounded-2xl p-4 sm:p-5 border border-slate-200/70 flex items-center justify-between gap-4 relative">
              <input
                type="file"
                ref={coverInputRef}
                accept=".png"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setCoverFile(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              <div className="flex items-center gap-3.5 min-w-0">
                {/* Preview Thumbnail */}
                <div 
                  onClick={() => coverInputRef.current?.click()}
                  className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden shrink-0 border border-slate-200 bg-slate-100 flex items-center justify-center cursor-pointer shadow-sm group"
                >
                  {coverPreview ? (
                    <img
                      src={coverPreview}
                      alt="Cover Preview"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-slate-400 group-hover:text-cubist-blue transition-colors">
                      <ImageIcon className="w-7 h-7" />
                    </div>
                  )}
                </div>

                {/* Info Text */}
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-ink-950 block truncate">
                      {coverFile ? 'Cover Image' : 'Select Cover Image'}
                    </span>
                  </div>
                  
                  {coverFile ? (
                    <p className="text-xs text-slate-500 font-mono mt-0.5">
                      PNG • {coverInfo ? `${coverInfo.width} × ${coverInfo.height}` : 'Reading...'}<br />
                      {formatBytes(coverFile.size)}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-400 mt-0.5">
                      Lossless PNG carrier
                    </p>
                  )}

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 mt-2.5">
                    <button
                      type="button"
                      onClick={() => coverInputRef.current?.click()}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
                    >
                      <ImageIcon className="w-3.5 h-3.5 text-slate-500" />
                      <span>{coverFile ? 'Change' : 'Choose'}</span>
                    </button>

                    {coverPreview && (
                      <button
                        type="button"
                        onClick={() => window.open(coverPreview, '_blank')}
                        className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-500 hover:text-slate-800 shadow-2xs transition-colors"
                        title="View image"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Status indicator checkmark */}
              {coverFile && (
                <div className="w-5 h-5 rounded-full bg-cubist-green flex items-center justify-center text-white shrink-0 self-start shadow-xs">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
              )}
            </div>

            {/* 2. File to Hide Panel */}
            <div className="bg-slate-50/80 rounded-2xl p-4 sm:p-5 border border-slate-200/70 flex items-center justify-between gap-4 relative">
              <input
                type="file"
                ref={payloadInputRef}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setPayloadFile(e.target.files[0]);
                  }
                }}
                className="hidden"
              />

              <div className="flex items-center gap-3.5 min-w-0">
                {/* File Thumbnail Box */}
                <div 
                  onClick={() => payloadInputRef.current?.click()}
                  className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden shrink-0 border border-slate-200 bg-rose-50/60 flex items-center justify-center cursor-pointer shadow-sm group"
                >
                  <FileText className="w-8 h-8 text-cubist-coral group-hover:scale-105 transition-transform" />
                </div>

                {/* Info Text */}
                <div className="min-w-0">
                  <span className="text-sm font-bold text-ink-950 block truncate">
                    {payloadFile ? 'File to Hide' : 'Select File to Hide'}
                  </span>

                  {payloadFile ? (
                    <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-[180px]">
                      {payloadFile.name}<br />
                      {formatBytes(payloadFile.size)}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-400 mt-0.5">
                      Any file (PDF, TXT, DOCX, ZIP...)
                    </p>
                  )}

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 mt-2.5">
                    <button
                      type="button"
                      onClick={() => payloadInputRef.current?.click()}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5 text-slate-500" />
                      <span>{payloadFile ? 'Change' : 'Choose'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Status indicator checkmark */}
              {payloadFile && (
                <div className="w-5 h-5 rounded-full bg-cubist-green flex items-center justify-center text-white shrink-0 self-start shadow-xs">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
              )}
            </div>

          </div>

          {/* Headroom / Capacity Analysis if both files loaded */}
          {headroom && (
            <div className="mb-6">
              <CapacityBar
                requiredBytes={headroom.total_required_bytes}
                capacityBytes={headroom.capacity_bytes}
                utilizationPct={headroom.utilization_pct}
              />
            </div>
          )}

          {/* Options & Security Strip (matches reference horizontal row) */}
          <div className="bg-slate-50/90 rounded-2xl p-4 sm:p-5 border border-slate-200/70 flex flex-col md:flex-row items-start md:items-center justify-between gap-5 mb-6">
            
            {/* Options Title & Desc */}
            <div className="flex items-center gap-3">
              <Sliders className="w-4 h-4 text-slate-600 shrink-0" />
              <div>
                <span className="text-xs font-bold text-ink-950 block">Options</span>
                <span className="text-[11px] text-slate-500 block">
                  Make your file smaller and/or more secure.
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-6 w-full md:w-auto">
              {/* Compress Toggle */}
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => setCompress(!compress)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    compress ? 'bg-cubist-ochre' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      compress ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
                <div className="leading-tight">
                  <span className="text-xs font-semibold text-ink-950 block">Compress</span>
                  <span className="text-[10px] text-slate-400 block">Reduce file size before hiding</span>
                </div>
              </div>

              <div className="h-6 w-[1px] bg-slate-200 hidden sm:block"></div>

              {/* Encrypt Toggle & Password Input */}
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => setEncrypt(!encrypt)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    encrypt ? 'bg-cubist-crimson' : 'bg-slate-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                      encrypt ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
                <div className="leading-tight">
                  <span className="text-xs font-semibold text-ink-950 block">Encrypt</span>
                  <span className="text-[10px] text-slate-400 block">Protect with a password</span>
                </div>

                {/* Password input capsule (matches reference) */}
                {encrypt && (
                  <div className="relative ml-2 flex items-center bg-white border border-slate-200 rounded-lg px-2.5 py-1 shadow-2xs">
                    <KeyRound className="w-3.5 h-3.5 text-slate-400 mr-1.5 shrink-0" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onFocus={() => {
                        if (password === '••••••••') setPassword('');
                      }}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Passphrase"
                      className="w-24 text-xs font-mono text-ink-950 focus:outline-none placeholder-slate-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="text-slate-400 hover:text-slate-700 ml-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* Primary Action Button (Matches the rounded pill CTA in reference) */}
          <button
            type="button"
            disabled={!coverFile || !payloadFile || isSubmitting || (headroom && !headroom.fits)}
            onClick={handleEncode}
            className={`w-full py-4 rounded-full font-display font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-lg transition-all duration-200 ${
              !coverFile || !payloadFile || (headroom && !headroom.fits)
                ? 'bg-ink-900 text-slate-500 cursor-not-allowed'
                : isSubmitting
                ? 'bg-ink-950 text-white cursor-wait opacity-90'
                : 'bg-ink-950 hover:bg-black text-white hover:shadow-xl active:scale-[0.99]'
            }`}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Hiding File in Image...</span>
              </>
            ) : (
              <>
                <span>Hide File</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Success Result Card */}
        {resultData && downloadUrl && (
          <div className="mt-8 p-6 sm:p-8 rounded-3xl bg-white border border-cubist-green/50 shadow-editorial animate-fadeIn space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-2xl bg-cubist-green/10 border border-cubist-green/30 flex items-center justify-center text-cubist-green shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold font-display text-ink-950">Carrier Ready with Hidden Payload</h3>
                  <p className="text-xs text-slate-500 mt-0.5">Payload lossless embedded using spatial 1-LSB substitution.</p>
                </div>
              </div>

              <a
                href={downloadUrl}
                download="stego.png"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-ink-950 hover:bg-black text-white font-display font-bold text-xs transition-colors shadow-md shrink-0"
              >
                <Download className="w-4 h-4" />
                <span>Download Stego Image</span>
              </a>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase">Payload</span>
                <span className="text-ink-950 font-semibold truncate block mt-0.5">{resultData.filename}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase">Original Size</span>
                <span className="text-ink-950 font-semibold block mt-0.5">{formatBytes(resultData.originalSize)}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase">Embedded Stream</span>
                <span className="text-cubist-blue font-semibold block mt-0.5">{formatBytes(resultData.embeddedSize)}</span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                <span className="text-slate-400 block text-[10px] uppercase">Latency</span>
                <span className="text-cubist-green font-semibold block mt-0.5">{resultData.encodeTimeMs} ms</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
              <span className="text-slate-500 text-[11px]">SHA-256 Digest:</span>
              <span className="text-cubist-blue select-all font-mono text-[11px] truncate max-w-sm sm:max-w-md">
                {resultData.sha256}
              </span>
            </div>
          </div>
        )}

        {/* Quote on the right bottom from the mockup */}
        <div className="mt-8 text-right hidden lg:block">
          <p className="text-xs font-serif italic text-slate-500 max-w-xs ml-auto leading-relaxed">
            “The most powerful information is the one no one sees.”
          </p>
          <div className="w-8 h-[1px] bg-slate-400 ml-auto mt-2"></div>
        </div>
      </div>
  );
}


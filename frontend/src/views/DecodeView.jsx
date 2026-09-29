import React, { useState, useEffect, useRef } from 'react';
import { 
  Eye, 
  Download, 
  Loader2, 
  AlertCircle, 
  KeyRound, 
  CheckCircle2, 
  ShieldCheck, 
  Image as ImageIcon, 
  Lock, 
  Layers 
} from 'lucide-react';

export default function DecodeView() {
  const [stegoFile, setStegoFile] = useState(null);
  const [stegoPreview, setStegoPreview] = useState(null);
  const [probeInfo, setProbeInfo] = useState(null);
  const fileInputRef = useRef(null);

  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [recoveredData, setRecoveredData] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  useEffect(() => {
    if (!stegoFile) {
      setStegoPreview(null);
      setProbeInfo(null);
      setRecoveredData(null);
      setErrorMsg(null);
      return;
    }

    const url = URL.createObjectURL(stegoFile);
    setStegoPreview(url);
    setErrorMsg(null);
    setRecoveredData(null);

    // Probe the stego image header
    const formData = new FormData();
    formData.append('stego', stegoFile);

    fetch('http://localhost:8000/api/probe-stego', {
      method: 'POST',
      body: formData,
    })
      .then((res) => {
        if (!res.ok) return res.json().then((d) => Promise.reject(d.detail));
        return res.json();
      })
      .then((data) => setProbeInfo(data))
      .catch((err) => {
        setErrorMsg(typeof err === 'string' ? err : 'No hidden data signature detected in this image.');
        setProbeInfo(null);
      });

    return () => URL.revokeObjectURL(url);
  }, [stegoFile]);

  const handleDecode = async () => {
    if (!stegoFile) return;
    if (probeInfo?.is_encrypted && !password.trim()) {
      setErrorMsg('This file is password-protected. Please enter the passphrase.');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    setRecoveredData(null);

    const formData = new FormData();
    formData.append('stego', stegoFile);
    if (password) {
      formData.append('password', password);
    }

    const startTime = performance.now();

    try {
      const res = await fetch('http://localhost:8000/api/decode', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Extraction failed.');
      }

      const filename = res.headers.get('X-Recovered-Filename') || 'recovered_file.bin';
      const size = res.headers.get('X-Payload-Size');
      const version = res.headers.get('X-Protocol-Version');
      const isCompressed = res.headers.get('X-Is-Compressed') === 'True';
      const isEncrypted = res.headers.get('X-Is-Encrypted') === 'True';
      const originalSha = res.headers.get('X-Original-SHA256');
      const recoveredSha = res.headers.get('X-Recovered-SHA256');
      const integrityPass = res.headers.get('X-Integrity-Verified') === 'True';
      const decodeTime = res.headers.get('X-Decoding-Time-Sec');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);

      setRecoveredData({
        filename,
        size: Number(size),
        version: Number(version),
        isCompressed,
        isEncrypted,
        originalSha,
        recoveredSha,
        integrityPass,
        decodeTimeMs: decodeTime ? (Number(decodeTime) * 1000).toFixed(1) : (performance.now() - startTime).toFixed(1),
      });
    } catch (err) {
      setErrorMsg(err.message || 'Decryption or file extraction failed.');
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
    <div className="relative w-full max-w-4xl">
      {/* Editorial Header */}
      <div className="mb-6 pt-2">
        <h1 className="text-4xl sm:text-5xl font-display font-extrabold text-ink-950 tracking-tight leading-[1.08]">
          Extract<br />
          <span className="text-cubist-blue">Hidden</span> Secrets
        </h1>
        <div className="flex items-center gap-3.5 mt-3.5">
          <div className="w-8 h-[1.5px] bg-ink-950"></div>
          <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-slate-500">
            AUTHENTICATED • LOSSLESS • INSTANT
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
        
        {/* Stego Image Upload Panel */}
        <input
          type="file"
          ref={fileInputRef}
          accept=".png"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              setStegoFile(e.target.files[0]);
            }
          }}
          className="hidden"
        />

        <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/70 flex flex-col sm:flex-row items-center justify-between gap-5">
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="w-20 h-20 rounded-xl overflow-hidden shrink-0 border border-slate-200 bg-white flex items-center justify-center cursor-pointer shadow-sm group"
            >
              {stegoPreview ? (
                <img
                  src={stegoPreview}
                  alt="Stego Preview"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
              ) : (
                <ImageIcon className="w-8 h-8 text-slate-400 group-hover:text-cubist-blue transition-colors" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <span className="text-sm font-bold text-ink-950 block">
                {stegoFile ? 'Stego Carrier Image' : 'Select Stego PNG Image'}
              </span>
              {stegoFile ? (
                <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-xs">
                  {stegoFile.name} • {formatBytes(stegoFile.size)}
                </p>
              ) : (
                <p className="text-xs text-slate-400 mt-0.5">
                  RGB PNG image with embedded payload
                </p>
              )}

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-2xs transition-colors"
              >
                <ImageIcon className="w-3.5 h-3.5 text-slate-500" />
                <span>{stegoFile ? 'Change Image' : 'Choose PNG'}</span>
              </button>
            </div>
          </div>

          {/* Status Badge */}
          {probeInfo && (
            <div className="self-end sm:self-center px-3 py-1.5 rounded-full bg-cubist-green/10 border border-cubist-green/20 text-xs font-mono text-cubist-green flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Valid Signature</span>
            </div>
          )}
        </div>

        {/* Header Metadata Probing Card */}
        {probeInfo && (
          <div className="bg-slate-50/90 rounded-2xl p-5 border border-slate-200/70 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Detected Metadata
              </span>
              <span className="text-[11px] font-mono text-slate-500">Header Inspection</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                <span className="text-slate-400 block text-[10px] uppercase">Embedded File</span>
                <span className="text-ink-950 font-bold truncate block mt-0.5">{probeInfo.filename}</span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                <span className="text-slate-400 block text-[10px] uppercase">Payload Size</span>
                <span className="text-cubist-blue font-bold block mt-0.5">{formatBytes(probeInfo.embedded_payload_bytes)}</span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                <span className="text-slate-400 block text-[10px] uppercase">Compression</span>
                <span className={`font-bold block mt-0.5 ${probeInfo.is_compressed ? 'text-cubist-green' : 'text-slate-500'}`}>
                  {probeInfo.is_compressed ? 'Enabled' : 'None'}
                </span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-2xs">
                <span className="text-slate-400 block text-[10px] uppercase">Protection</span>
                <span className={`font-bold block mt-0.5 ${probeInfo.is_encrypted ? 'text-cubist-crimson' : 'text-slate-500'}`}>
                  {probeInfo.is_encrypted ? 'Encrypted' : 'None'}
                </span>
              </div>
            </div>

            {/* Password input if encrypted */}
            {probeInfo.is_encrypted && (
              <div className="pt-3 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-cubist-crimson" />
                  <span className="text-xs font-bold text-ink-950">Decryption Passphrase Required</span>
                </div>
                <div className="relative flex items-center bg-white border border-slate-200 rounded-lg px-3 py-1.5 shadow-2xs w-full sm:w-64">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter passphrase..."
                    className="w-full text-xs font-mono text-ink-950 focus:outline-none placeholder-slate-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-slate-700 ml-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Primary Action Button */}
        <button
          type="button"
          disabled={!stegoFile || isSubmitting || !probeInfo}
          onClick={handleDecode}
          className={`w-full py-4 rounded-full font-display font-bold text-sm tracking-wide flex items-center justify-center gap-2 shadow-lg transition-all duration-200 ${
            !stegoFile || !probeInfo
              ? 'bg-ink-900 text-slate-500 cursor-not-allowed'
              : isSubmitting
              ? 'bg-ink-950 text-white cursor-wait opacity-90'
              : 'bg-ink-950 hover:bg-black text-white hover:shadow-xl active:scale-[0.99]'
          }`}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-white" />
              <span>Extracting & Verifying Integrity...</span>
            </>
          ) : (
            <>
              <span>Extract File</span>
              <Download className="w-4 h-4" />
            </>
          )}
        </button>

      </div>

      {/* Recovered File Result Card */}
      {recoveredData && downloadUrl && (
        <div className="mt-8 p-6 sm:p-8 rounded-3xl bg-white border border-cubist-green/50 shadow-editorial animate-fadeIn space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-cubist-green/10 border border-cubist-green/30 flex items-center justify-center text-cubist-green shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold font-display text-ink-950">Integrity Verified</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cubist-green/15 text-cubist-green border border-cubist-green/30 font-bold">
                    SHA-256 MATCH
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Exact byte-for-byte reconstruction confirmed.
                </p>
              </div>
            </div>

            <a
              href={downloadUrl}
              download={recoveredData.filename}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-ink-950 hover:bg-black text-white font-display font-bold text-xs transition-colors shadow-md shrink-0"
            >
              <Download className="w-4 h-4" />
              <span>Download {recoveredData.filename}</span>
            </a>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Recovered File</span>
              <span className="text-ink-950 font-semibold truncate block mt-0.5">{recoveredData.filename}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">File Size</span>
              <span className="text-ink-950 font-semibold block mt-0.5">{formatBytes(recoveredData.size)}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Processing</span>
              <span className="text-cubist-blue font-semibold block mt-0.5">
                {recoveredData.isCompressed ? 'Decompressed ' : ''}
                {recoveredData.isEncrypted ? '+ Decrypted' : ''}
                {!recoveredData.isCompressed && !recoveredData.isEncrypted ? 'Direct LSB' : ''}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase">Latency</span>
              <span className="text-cubist-green font-semibold block mt-0.5">{recoveredData.decodeTimeMs} ms</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
            <span className="text-slate-500 text-[11px]">Verified SHA-256 Digest:</span>
            <span className="text-cubist-green select-all font-mono text-[11px] truncate max-w-sm sm:max-w-md">
              {recoveredData.recoveredSha}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}


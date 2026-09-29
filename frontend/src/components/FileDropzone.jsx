import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, Check, ArrowUpRight } from 'lucide-react';

export default function FileDropzone({
  title,
  subtitle,
  accept,
  selectedFile,
  onFileSelect,
  previewUrl,
  badgeText,
}) {
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const formatBytes = (bytes) => {
    if (!bytes && bytes !== 0) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-paper-300 font-sans">
          {title}
        </label>
        {badgeText && (
          <span className="text-[10px] font-mono tracking-tight px-2 py-0.5 rounded bg-veil-800 text-paper-400 border border-veil-700/60">
            {badgeText}
          </span>
        )}
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`group relative rounded-xl p-5 cursor-pointer transition-all duration-300 flex flex-col items-center justify-center min-h-[160px] border ${
          isDragOver
            ? 'border-cubist-ochre bg-cubist-ochre/5 scale-[1.01]'
            : selectedFile
            ? 'border-veil-700 bg-veil-850/80 hover:border-paper-300/40'
            : 'border-veil-800/80 bg-veil-850/40 hover:border-veil-700 hover:bg-veil-850/70'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          accept={accept}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              onFileSelect(e.target.files[0]);
            }
          }}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full px-2">
            {previewUrl ? (
              <div className="relative shrink-0 w-20 h-20 rounded-lg overflow-hidden border border-veil-700 bg-veil-900 shadow-sm">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="shrink-0 w-14 h-14 rounded-lg bg-veil-800 border border-veil-700 flex items-center justify-center text-cubist-ochre shadow-sm">
                <FileText className="w-6 h-6" />
              </div>
            )}

            <div className="text-center sm:text-left flex-1 min-w-0">
              <div className="flex items-center justify-center sm:justify-start gap-1.5 text-paper-100 text-sm font-semibold">
                <Check className="w-4 h-4 text-cubist-sage shrink-0" />
                <span className="truncate">{selectedFile.name}</span>
              </div>
              <p className="text-xs text-paper-400 font-mono mt-0.5">
                {formatBytes(selectedFile.size)}
              </p>
              <div className="mt-2 inline-flex items-center gap-1 text-[11px] text-cubist-ochre font-medium group-hover:underline">
                <span>Replace file</span>
                <ArrowUpRight className="w-3 h-3" />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2.5 text-center">
            <div className="w-10 h-10 rounded-xl bg-veil-800/80 border border-veil-700/60 flex items-center justify-center text-paper-400 group-hover:text-paper-100 group-hover:border-paper-400/40 transition-colors">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-paper-100">
                Drop file here, or <span className="text-cubist-ochre underline underline-offset-4 decoration-cubist-ochre/40 group-hover:decoration-cubist-ochre">browse</span>
              </p>
              <p className="text-xs text-paper-400 mt-1 font-sans">{subtitle}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// PhotoCanvas.tsx — Main image display area for Lumara.
// Shows the current image preview, a drop-zone when no image is loaded, and zoom controls.
// Exports: PhotoCanvas component.

import { useState, useCallback, useRef } from "react";
import { useSessionStore } from "@/store/sessionStore";

interface PhotoCanvasProps {
  onOpenFile: () => void;
}

const styles = {
  wrapper: "relative flex-1 flex items-center justify-center bg-[#111] overflow-hidden",
  image: "max-w-full max-h-full object-contain select-none",
  dropZone: "flex flex-col items-center justify-center gap-4 text-muted cursor-pointer w-full h-full",
  dropIcon: "w-16 h-16 opacity-20",
  dropText: "text-sm",
  dropHint: "text-xs opacity-50",
  toolbar: "absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-surface-overlay/80 backdrop-blur rounded-full px-4 py-2",
  toolbarBtn: "text-xs text-muted hover:text-white transition-colors px-1",
  zoomLabel: "text-xs font-mono text-muted w-12 text-center",
  dragOver: "ring-2 ring-accent ring-inset",
};

export function PhotoCanvas({ onOpenFile }: PhotoCanvasProps) {
  const { previewDataUrl, currentImage } = useSessionStore();
  const [zoom, setZoom] = useState(1.0);
  const [isDragOver, setIsDragOver] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 4));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.25));
  const handleZoomReset = () => setZoom(1.0);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragOver(false), []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      // File handling delegated to useImageProcessor via onOpenFile
      // Tauri will intercept the file drop natively
      onOpenFile();
    },
    [onOpenFile]
  );

  return (
    <div
      ref={wrapperRef}
      className={`${styles.wrapper} ${isDragOver ? styles.dragOver : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {previewDataUrl ? (
        <>
          <img
            src={previewDataUrl}
            alt={currentImage?.fileName ?? "Preview"}
            className={styles.image}
            style={{ transform: `scale(${zoom})`, transition: "transform 0.15s ease" }}
            draggable={false}
          />

          {/* Zoom toolbar */}
          <div className={styles.toolbar}>
            <button className={styles.toolbarBtn} onClick={handleZoomOut} title="Zoom out">
              −
            </button>
            <button className={styles.zoomLabel} onClick={handleZoomReset} title="Reset zoom">
              {Math.round(zoom * 100)}%
            </button>
            <button className={styles.toolbarBtn} onClick={handleZoomIn} title="Zoom in">
              +
            </button>
          </div>
        </>
      ) : (
        <div className={styles.dropZone} onClick={onOpenFile}>
          {/* Simple SVG placeholder icon */}
          <svg
            className={styles.dropIcon}
            viewBox="0 0 64 64"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="8" y="12" width="48" height="40" rx="4" />
            <circle cx="22" cy="26" r="5" />
            <path d="M8 40 l14-14 10 10 8-8 16 14" />
          </svg>
          <p className={styles.dropText}>Drop an image here or click to open</p>
          <p className={styles.dropHint}>
            Supports RAW (CR2, NEF, ARW, DNG), JPEG, PNG, WEBP, TIFF, HEIF
          </p>
        </div>
      )}
    </div>
  );
}

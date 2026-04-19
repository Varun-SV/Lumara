// App.tsx — Root layout for Lumara. Composes the three-panel editor UI:
//   Left: file browser / history panel
//   Centre: PhotoCanvas (main image view)
//   Right: EditPanel + SuggestionCard
// Exports: default App component.

import { useCallback } from "react";
import { PhotoCanvas } from "@/components/PhotoCanvas";
import { EditPanel } from "@/components/EditPanel";
import { SuggestionCard } from "@/components/SuggestionCard";
import { HistoryPanel } from "@/components/HistoryPanel";
import { useSessionStore } from "@/store/sessionStore";
import { useImageProcessor } from "@/hooks/useImageProcessor";

const styles = {
  root: "flex flex-col h-screen w-screen bg-surface overflow-hidden",
  titleBar: "flex items-center justify-between px-4 h-10 bg-surface-elevated border-b border-border shrink-0 select-none",
  appName: "text-sm font-semibold tracking-widest text-accent uppercase",
  body: "flex flex-1 overflow-hidden",
  leftPanel: "w-52 shrink-0 flex flex-col border-r border-border overflow-y-auto",
  centre: "flex-1 flex flex-col overflow-hidden",
  rightPanel: "w-72 shrink-0 flex flex-col border-l border-border overflow-y-auto",
  llmBadge: "text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent font-mono",
  statusIdle: "text-xs text-muted",
  statusLoading: "text-xs text-accent animate-pulse",
  statusError: "text-xs text-red-400",
};

export default function App() {
  const { llmStatus, llmError, currentImage } = useSessionStore();
  const { openImage } = useImageProcessor();

  const handleOpenFile = useCallback(async () => {
    await openImage();
  }, [openImage]);

  const statusLabel =
    llmStatus === "loading"
      ? "AI thinking…"
      : llmStatus === "error"
      ? `AI error: ${llmError ?? "unknown"}`
      : currentImage
      ? `${currentImage.fileName}`
      : "No image open";

  const statusClass =
    llmStatus === "loading"
      ? styles.statusLoading
      : llmStatus === "error"
      ? styles.statusError
      : styles.statusIdle;

  return (
    <div className={styles.root}>
      {/* Title bar */}
      <header className={styles.titleBar}>
        <span className={styles.appName}>Lumara</span>
        <span className={statusClass}>{statusLabel}</span>
        <span className={styles.llmBadge}>local AI</span>
      </header>

      {/* Main body */}
      <div className={styles.body}>
        {/* Left: history */}
        <aside className={styles.leftPanel}>
          <HistoryPanel />
        </aside>

        {/* Centre: canvas */}
        <main className={styles.centre}>
          <PhotoCanvas onOpenFile={handleOpenFile} />
        </main>

        {/* Right: edits + suggestions */}
        <aside className={styles.rightPanel}>
          <SuggestionCard />
          <EditPanel />
        </aside>
      </div>
    </div>
  );
}

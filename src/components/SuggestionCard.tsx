// SuggestionCard.tsx — Displays AI-generated edit suggestions for the loaded image.
// Each suggestion shows its label, reason, priority badge, and an apply button.
// Exports: SuggestionCard component.

import { useCallback } from "react";
import { useSessionStore } from "@/store/sessionStore";
import { useEditStore } from "@/store/editStore";
import { EditSuggestion, Priority } from "@/types/lumara";

const priorityColor: Record<Priority, string> = {
  HIGH: "bg-red-500/20 text-red-400",
  MEDIUM: "bg-amber-500/20 text-amber-400",
  LOW: "bg-blue-500/20 text-blue-400",
};

const styles = {
  root: "flex flex-col border-b border-border",
  header: "flex items-center justify-between px-4 py-3 cursor-pointer select-none",
  title: "text-xs font-semibold uppercase tracking-wider text-muted",
  toggle: "text-muted text-xs",
  body: "px-3 pb-3 flex flex-col gap-2",
  empty: "text-xs text-muted px-4 py-3 italic",
  card: "rounded-lg bg-surface-overlay p-3 flex flex-col gap-2",
  cardTop: "flex items-start justify-between gap-2",
  label: "text-sm font-medium text-white leading-tight",
  badge: "text-[10px] font-mono px-1.5 py-0.5 rounded-full shrink-0",
  reason: "text-xs text-muted leading-relaxed",
  applyBtn:
    "self-end text-xs px-3 py-1 rounded-md bg-accent/10 text-accent border border-accent/30 hover:bg-accent/20 transition-colors",
  loadingText: "text-xs text-accent animate-pulse px-4 py-3",
};

function SuggestionItem({ suggestion }: { suggestion: EditSuggestion }) {
  const { pushEdit } = useEditStore();

  const handleApply = useCallback(() => {
    pushEdit(
      suggestion.label,
      "parametric",
      suggestion.reason,
      suggestion.edit
    );
  }, [suggestion, pushEdit]);

  return (
    <div className={styles.card}>
      <div className={styles.cardTop}>
        <span className={styles.label}>{suggestion.label}</span>
        <span className={`${styles.badge} ${priorityColor[suggestion.priority]}`}>
          {suggestion.priority}
        </span>
      </div>
      <p className={styles.reason}>{suggestion.reason}</p>
      <button className={styles.applyBtn} onClick={handleApply}>
        Apply
      </button>
    </div>
  );
}

export function SuggestionCard() {
  const { suggestions, llmStatus, suggestionPanelOpen, toggleSuggestionPanel } =
    useSessionStore();

  return (
    <section className={styles.root}>
      <div className={styles.header} onClick={toggleSuggestionPanel}>
        <span className={styles.title}>AI Suggestions</span>
        <span className={styles.toggle}>{suggestionPanelOpen ? "▲" : "▼"}</span>
      </div>

      {suggestionPanelOpen && (
        <>
          {llmStatus === "loading" && (
            <p className={styles.loadingText}>Analysing image…</p>
          )}

          {llmStatus !== "loading" && suggestions.length === 0 && (
            <p className={styles.empty}>
              Open an image to receive AI edit suggestions.
            </p>
          )}

          <div className={styles.body}>
            {suggestions.map((s) => (
              <SuggestionItem key={s.id} suggestion={s} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

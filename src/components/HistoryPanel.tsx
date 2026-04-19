// HistoryPanel.tsx — Left-panel edit history viewer.
// Shows the ordered edit stack; supports click-to-jump, undo, redo, and clear.
// Exports: HistoryPanel component.

import { useCallback } from "react";
import { useEditStore } from "@/store/editStore";
import { AppliedEdit } from "@/types/lumara";

const styles = {
  root: "flex flex-col h-full",
  header: "px-4 py-3 border-b border-border",
  title: "text-xs font-semibold uppercase tracking-wider text-muted",
  actions: "flex gap-2 mt-2",
  actionBtn:
    "text-xs px-2 py-1 rounded bg-surface-overlay hover:bg-border transition-colors text-muted hover:text-white disabled:opacity-30 disabled:cursor-not-allowed",
  list: "flex-1 overflow-y-auto py-2",
  empty: "text-xs text-muted italic px-4 py-3",
  item: "flex items-start gap-2 px-3 py-2 cursor-pointer hover:bg-surface-overlay rounded-md mx-2 group transition-colors",
  itemActive: "bg-surface-overlay",
  itemFuture: "opacity-40",
  dot: "w-2 h-2 rounded-full bg-accent shrink-0 mt-1",
  dotFuture: "w-2 h-2 rounded-full bg-muted/40 shrink-0 mt-1",
  layerName: "text-xs font-medium text-white leading-tight truncate",
  desc: "text-[11px] text-muted leading-relaxed",
  timestamp: "text-[10px] text-muted/40 mt-0.5",
  removeBtn:
    "ml-auto text-muted/0 group-hover:text-muted/60 hover:!text-red-400 transition-colors text-xs shrink-0",
};

function HistoryItem({
  edit,
  isActive,
  isFuture,
  onRemove,
}: {
  edit: AppliedEdit;
  isActive: boolean;
  isFuture: boolean;
  onRemove: (id: string) => void;
}) {
  const handleRemove = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onRemove(edit.id);
    },
    [edit.id, onRemove]
  );

  const time = new Date(edit.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div
      className={`${styles.item} ${isActive ? styles.itemActive : ""} ${isFuture ? styles.itemFuture : ""}`}
    >
      <span className={isFuture ? styles.dotFuture : styles.dot} />
      <div className="flex-1 min-w-0">
        <p className={styles.layerName}>{edit.layer_name}</p>
        <p className={styles.desc}>{edit.description}</p>
        <p className={styles.timestamp}>{time}</p>
      </div>
      {edit.reversible && (
        <button className={styles.removeBtn} onClick={handleRemove} title="Remove edit">
          ✕
        </button>
      )}
    </div>
  );
}

export function HistoryPanel() {
  const { editStack, headIndex, undoEdit, redoEdit, clearStack, removeEdit, canUndo, canRedo } =
    useEditStore();

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <p className={styles.title}>History</p>
        <div className={styles.actions}>
          <button
            className={styles.actionBtn}
            onClick={undoEdit}
            disabled={!canUndo()}
            title="Undo"
          >
            ↩ Undo
          </button>
          <button
            className={styles.actionBtn}
            onClick={redoEdit}
            disabled={!canRedo()}
            title="Redo"
          >
            ↪ Redo
          </button>
          <button
            className={styles.actionBtn}
            onClick={clearStack}
            disabled={editStack.length === 0}
            title="Clear all"
          >
            ✕
          </button>
        </div>
      </div>

      <div className={styles.list}>
        {editStack.length === 0 ? (
          <p className={styles.empty}>No edits yet.</p>
        ) : (
          [...editStack].reverse().map((edit, reversedIdx) => {
            const originalIdx = editStack.length - 1 - reversedIdx;
            return (
              <HistoryItem
                key={edit.id}
                edit={edit}
                isActive={originalIdx === headIndex}
                isFuture={originalIdx > headIndex}
                onRemove={removeEdit}
              />
            );
          })
        )}
      </div>
    </div>
  );
}

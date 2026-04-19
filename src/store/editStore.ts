// editStore.ts — Zustand store for the non-destructive edit stack.
// Exports: useEditStore hook, EditState interface.

import { create } from "zustand";
import { AppliedEdit, EditParameters, EditLayerType } from "@/types/lumara";
import { v4 as uuidv4 } from "crypto";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeId(): string {
  // crypto.randomUUID is available in Tauri's WebView context
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : uuidv4();
}

function nowISO(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export interface EditState {
  /** Ordered list of edits applied to the current image. */
  editStack: AppliedEdit[];
  /** Index of the currently "active" position in the stack (-1 = none). */
  headIndex: number;

  // Mutations
  pushEdit: (
    layer_name: string,
    type: EditLayerType,
    description: string,
    parameters: EditParameters,
    code?: string
  ) => void;
  undoEdit: () => void;
  redoEdit: () => void;
  removeEdit: (id: string) => void;
  clearStack: () => void;
  loadStack: (stack: AppliedEdit[]) => void;

  // Selectors
  activeStack: () => AppliedEdit[];
  canUndo: () => boolean;
  canRedo: () => boolean;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useEditStore = create<EditState>((set, get) => ({
  editStack: [],
  headIndex: -1,

  pushEdit: (layer_name, type, description, parameters, code) => {
    const newEdit: AppliedEdit = {
      id: makeId(),
      type,
      description,
      parameters,
      code,
      layer_name,
      reversible: true,
      timestamp: nowISO(),
    };

    set((state) => {
      // Discard any edits "above" the current head (redo history)
      const truncated = state.editStack.slice(0, state.headIndex + 1);
      const newStack = [...truncated, newEdit];
      return {
        editStack: newStack,
        headIndex: newStack.length - 1,
      };
    });
  },

  undoEdit: () => {
    set((state) => {
      if (state.headIndex < 0) return state;
      return { headIndex: state.headIndex - 1 };
    });
  },

  redoEdit: () => {
    set((state) => {
      if (state.headIndex >= state.editStack.length - 1) return state;
      return { headIndex: state.headIndex + 1 };
    });
  },

  removeEdit: (id) => {
    set((state) => {
      const idx = state.editStack.findIndex((e) => e.id === id);
      if (idx === -1) return state;
      const newStack = state.editStack.filter((e) => e.id !== id);
      // Adjust head so it doesn't point beyond the end
      const newHead = Math.min(state.headIndex, newStack.length - 1);
      return { editStack: newStack, headIndex: newHead };
    });
  },

  clearStack: () => set({ editStack: [], headIndex: -1 }),

  loadStack: (stack) =>
    set({ editStack: stack, headIndex: stack.length - 1 }),

  activeStack: () => {
    const { editStack, headIndex } = get();
    return editStack.slice(0, headIndex + 1);
  },

  canUndo: () => get().headIndex >= 0,
  canRedo: () => get().headIndex < get().editStack.length - 1,
}));

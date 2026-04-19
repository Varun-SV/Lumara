// sessionStore.ts — Zustand store for the current session (loaded image, AI state).
// Exports: useSessionStore hook, SessionState interface.

import { create } from "zustand";
import {
  LoadedImage,
  EditSuggestion,
  ImageAnalysis,
} from "@/types/lumara";

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export type LLMStatus = "idle" | "loading" | "error";

export interface SessionState {
  /** The currently open image, or null if no image is loaded. */
  currentImage: LoadedImage | null;

  /** AI-generated edit suggestions for the current image. */
  suggestions: EditSuggestion[];

  /** The latest analysis result from the LLM. */
  analysis: ImageAnalysis | null;

  /** Current LLM request status. */
  llmStatus: LLMStatus;
  llmError: string | null;

  /** The live preview data URL (updated after each edit application). */
  previewDataUrl: string | null;

  /** Whether the AI suggestion panel is expanded. */
  suggestionPanelOpen: boolean;

  // Mutations
  setImage: (image: LoadedImage) => void;
  clearImage: () => void;
  setSuggestions: (suggestions: EditSuggestion[]) => void;
  setAnalysis: (analysis: ImageAnalysis) => void;
  setLLMStatus: (status: LLMStatus, error?: string) => void;
  setPreview: (dataUrl: string) => void;
  toggleSuggestionPanel: () => void;
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useSessionStore = create<SessionState>((set) => ({
  currentImage: null,
  suggestions: [],
  analysis: null,
  llmStatus: "idle",
  llmError: null,
  previewDataUrl: null,
  suggestionPanelOpen: true,

  setImage: (image) =>
    set({
      currentImage: image,
      suggestions: [],
      analysis: image.analysis ?? null,
      previewDataUrl: image.previewDataUrl,
      llmStatus: "idle",
      llmError: null,
    }),

  clearImage: () =>
    set({
      currentImage: null,
      suggestions: [],
      analysis: null,
      previewDataUrl: null,
      llmStatus: "idle",
      llmError: null,
    }),

  setSuggestions: (suggestions) => set({ suggestions }),

  setAnalysis: (analysis) => set({ analysis }),

  setLLMStatus: (status, error = null) =>
    set({ llmStatus: status, llmError: error ?? null }),

  setPreview: (dataUrl) => set({ previewDataUrl: dataUrl }),

  toggleSuggestionPanel: () =>
    set((state) => ({ suggestionPanelOpen: !state.suggestionPanelOpen })),
}));

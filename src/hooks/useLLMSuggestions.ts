// useLLMSuggestions.ts — Hook for communicating with the local LLM via the Python sidecar.
// Sends the image path + optional user message; parses the structured JSON response.
// Exports: useLLMSuggestions hook.

import { useCallback } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { useSessionStore } from "@/store/sessionStore";
import { LLMAnalysisRequest, LLMAnalysisResponse } from "@/types/lumara";

export function useLLMSuggestions() {
  const { setSuggestions, setAnalysis, setLLMStatus } = useSessionStore();

  /**
   * Send the image to the LLM for initial analysis + suggestion generation.
   * Populates sessionStore with suggestions, analysis, caption, and tags.
   */
  const analyseImage = useCallback(
    async (imagePath: string, userMessage?: string) => {
      setLLMStatus("loading");

      const req: LLMAnalysisRequest = {
        image_path: imagePath,
        user_message: userMessage,
      };

      try {
        const res = await invoke<LLMAnalysisResponse>("llm_analyse", { request: req });

        if (res.analysis) setAnalysis(res.analysis);
        if (res.suggestions) setSuggestions(res.suggestions);

        // Update the loaded image record with caption/tags if present
        if (res.caption || res.tags) {
          const { currentImage, setImage } = useSessionStore.getState();
          if (currentImage) {
            setImage({
              ...currentImage,
              analysis: res.analysis ?? currentImage.analysis,
              caption: res.caption ?? currentImage.caption,
              tags: res.tags ?? currentImage.tags,
            });
          }
        }

        setLLMStatus("idle");
        return res;
      } catch (err) {
        setLLMStatus("error", String(err));
        return null;
      }
    },
    [setSuggestions, setAnalysis, setLLMStatus]
  );

  /**
   * Send a freeform natural-language edit command to the LLM.
   * Returns applied_edit instructions which the caller should push to the edit stack.
   */
  const sendEditCommand = useCallback(
    async (imagePath: string, command: string): Promise<LLMAnalysisResponse | null> => {
      setLLMStatus("loading");

      const req: LLMAnalysisRequest = {
        image_path: imagePath,
        user_message: command,
      };

      try {
        const res = await invoke<LLMAnalysisResponse>("llm_analyse", { request: req });
        setLLMStatus("idle");
        return res;
      } catch (err) {
        setLLMStatus("error", String(err));
        return null;
      }
    },
    [setLLMStatus]
  );

  return { analyseImage, sendEditCommand };
}

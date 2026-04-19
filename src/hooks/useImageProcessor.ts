// useImageProcessor.ts — Hook that bridges the React UI to the Python sidecar via Tauri IPC.
// Handles: opening files via Tauri dialog, sending the edit stack for rendering, and
// loading sidecar .lumara.json files alongside source images.
// Exports: useImageProcessor hook.

import { useCallback } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { open } from "@tauri-apps/api/dialog";
import { useSessionStore } from "@/store/sessionStore";
import { useEditStore } from "@/store/editStore";
import {
  LoadedImage,
  ProcessImageRequest,
  ProcessImageResponse,
  SidecarData,
} from "@/types/lumara";
import { useLLMSuggestions } from "./useLLMSuggestions";

const SUPPORTED_EXTENSIONS = [
  "cr2", "nef", "arw", "dng", "rw2", "orf",
  "jpg", "jpeg", "png", "webp", "tiff", "tif", "heif", "heic",
];

export function useImageProcessor() {
  const { setImage, setPreview, setLLMStatus } = useSessionStore();
  const { loadStack, clearStack } = useEditStore();
  const { analyseImage } = useLLMSuggestions();

  /** Open a file picker and load the chosen image. */
  const openImage = useCallback(async () => {
    let filePath: string | null = null;

    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: "Images", extensions: SUPPORTED_EXTENSIONS }],
      });

      if (!selected || Array.isArray(selected)) return;
      filePath = selected;
    } catch (err) {
      console.error("[useImageProcessor] dialog error", err);
      return;
    }

    try {
      setLLMStatus("loading");

      // Ask the sidecar to load + decode the image and return metadata + preview
      const loaded = await invoke<LoadedImage>("load_image", { filePath });

      // Check for an existing .lumara.json sidecar
      try {
        const sidecar = await invoke<SidecarData>("load_sidecar", { filePath });
        if (sidecar?.edit_stack?.length) {
          loadStack(sidecar.edit_stack);
        } else {
          clearStack();
        }
      } catch {
        // No sidecar — start fresh
        clearStack();
      }

      setImage(loaded);

      // Trigger LLM analysis in the background
      await analyseImage(filePath);
    } catch (err) {
      setLLMStatus("error", String(err));
    }
  }, [setImage, setLLMStatus, loadStack, clearStack, analyseImage]);

  /** Re-render the preview by sending the current edit stack to the sidecar. */
  const applyEdits = useCallback(async () => {
    const { currentImage } = useSessionStore.getState();
    const activeEdits = useEditStore.getState().activeStack();

    if (!currentImage) return;

    const req: ProcessImageRequest = {
      image_path: currentImage.filePath,
      edit_stack: activeEdits,
    };

    try {
      const res = await invoke<ProcessImageResponse>("apply_edits", { request: req });
      setPreview(res.preview_data_url);

      if (res.warnings?.length) {
        console.warn("[useImageProcessor] sidecar warnings:", res.warnings);
      }
    } catch (err) {
      console.error("[useImageProcessor] apply_edits error", err);
    }
  }, [setPreview]);

  /** Save the current edit stack to a .lumara.json sidecar. */
  const saveSidecar = useCallback(async () => {
    const { currentImage } = useSessionStore.getState();
    const { editStack } = useEditStore.getState();

    if (!currentImage) return;

    try {
      await invoke("save_sidecar", {
        filePath: currentImage.filePath,
        editStack,
      });
    } catch (err) {
      console.error("[useImageProcessor] save_sidecar error", err);
    }
  }, []);

  return { openImage, applyEdits, saveSidecar };
}

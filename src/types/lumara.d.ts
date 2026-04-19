// lumara.d.ts — Global TypeScript types for the Lumara photo editor.
// Exports: all LLM response types, edit parameter schema, session types, and IPC message shapes.

// ---------------------------------------------------------------------------
// Edit parameter schema — mirrors the JSON schema in the AI system prompt
// ---------------------------------------------------------------------------

export interface ToneCurvePoints {
  luma?: [number, number][];
  red?: [number, number][];
  green?: [number, number][];
  blue?: [number, number][];
}

export interface HSLBand {
  hue?: number;       // -180 to +180
  saturation?: number; // -100 to +100
  luminance?: number;  // -100 to +100
}

export interface HSLAdjustments {
  red?: HSLBand;
  orange?: HSLBand;
  yellow?: HSLBand;
  green?: HSLBand;
  aqua?: HSLBand;
  blue?: HSLBand;
  purple?: HSLBand;
  magenta?: HSLBand;
}

export interface PortraitAdjustments {
  skin_smoothing?: number;    // 0–100
  blemish_removal?: boolean;
  eye_enhancement?: number;   // 0–100
  teeth_whitening?: number;   // 0–100
  face_brightness?: number;   // -50 to +50
}

export type CropAspect = "original" | "1:1" | "4:3" | "16:9" | "3:2" | "freeform";

export type PresetName =
  | "cinematic"
  | "film_fade"
  | "moody_dark"
  | "airy_bright"
  | "warm_portrait"
  | "cool_landscape"
  | "bw_classic"
  | "bw_high_contrast"
  | "vsco_a6"
  | "vintage_faded";

export interface EditParameters {
  // Basic adjustments
  exposure?: number;       // -5.0 to +5.0 EV
  contrast?: number;       // -100 to +100
  highlights?: number;     // -100 to +100
  shadows?: number;        // -100 to +100
  whites?: number;         // -100 to +100
  blacks?: number;         // -100 to +100
  clarity?: number;        // -100 to +100
  texture?: number;        // -100 to +100
  dehaze?: number;         // -100 to +100
  vibrance?: number;       // -100 to +100
  saturation?: number;     // -100 to +100

  // White balance
  temperature?: number;    // 2000–50000 K or -100 to +100 relative
  tint?: number;           // -150 to +150

  // Sharpening
  sharpening_amount?: number;   // 0–150
  sharpening_radius?: number;   // 0.5–3.0
  sharpening_masking?: number;  // 0–100

  // Noise reduction
  noise_luminance?: number;  // 0–100
  noise_color?: number;      // 0–100

  // Vignette
  vignette_amount?: number;    // -100 to +100
  vignette_midpoint?: number;  // 0–100

  // Geometry
  crop_aspect?: CropAspect;
  straighten_angle?: number;   // -45.0 to +45.0 degrees

  // Advanced
  tone_curve?: ToneCurvePoints;
  hsl?: HSLAdjustments;
  portrait?: PortraitAdjustments;
  preset?: PresetName;
}

// ---------------------------------------------------------------------------
// LLM response types
// ---------------------------------------------------------------------------

export type SceneType =
  | "portrait"
  | "landscape"
  | "macro"
  | "street"
  | "architecture"
  | "product"
  | "abstract"
  | "night";

export type Priority = "HIGH" | "MEDIUM" | "LOW";

export interface ImageAnalysis {
  scene_type: SceneType;
  lighting: string;
  issues: string[];
  mood: string;
  composition_notes: string;
}

export interface EditSuggestion {
  id: string;
  label: string;
  reason: string;
  priority: Priority;
  edit: EditParameters;
}

export type EditLayerType = "parametric" | "code";

export interface AppliedEdit {
  id: string;             // UUID assigned by the host app
  type: EditLayerType;
  description: string;
  parameters: EditParameters;
  code?: string;          // Only present when type === "code"
  layer_name: string;
  reversible: boolean;
  timestamp: string;      // ISO 8601
}

export interface LLMResponse {
  analysis?: ImageAnalysis;
  suggestions?: EditSuggestion[];
  applied_edits?: Omit<AppliedEdit, "id" | "timestamp">[];
  caption?: string;
  tags?: string[];
  answer?: string;
  warnings?: string[];
}

// ---------------------------------------------------------------------------
// Session & image state
// ---------------------------------------------------------------------------

export type ImageFormat =
  | "CR2" | "NEF" | "ARW" | "DNG" | "RW2" | "ORF"
  | "JPEG" | "PNG" | "WEBP" | "TIFF" | "HEIF";

export interface LoadedImage {
  id: string;            // UUID
  filePath: string;
  fileName: string;
  format: ImageFormat;
  widthPx: number;
  heightPx: number;
  previewDataUrl: string; // Base64 preview rendered by Python sidecar
  analysis?: ImageAnalysis;
  caption?: string;
  tags?: string[];
}

export interface SidecarData {
  version: 1;
  source_file: string;
  created_at: string;
  updated_at: string;
  edit_stack: AppliedEdit[];
}

// ---------------------------------------------------------------------------
// IPC message shapes (Tauri ↔ Python sidecar)
// ---------------------------------------------------------------------------

export interface ProcessImageRequest {
  image_path: string;
  edit_stack: AppliedEdit[];
  output_format?: string;
  output_quality?: number;
}

export interface ProcessImageResponse {
  preview_data_url: string;
  warnings: string[];
}

export interface LLMAnalysisRequest {
  image_path: string;
  user_message?: string;
}

export type LLMAnalysisResponse = LLMResponse;

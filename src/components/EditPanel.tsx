// EditPanel.tsx — Right-hand panel with sliders for all basic/advanced adjustments.
// Reads from editStore to show current values and dispatches pushEdit on change.
// Exports: EditPanel component.

import { useCallback, useMemo } from "react";
import { useEditStore } from "@/store/editStore";
import { EditParameters } from "@/types/lumara";

// ---------------------------------------------------------------------------
// Generic slider row
// ---------------------------------------------------------------------------

interface SliderRowProps {
  label: string;
  param: keyof EditParameters;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (param: keyof EditParameters, value: number) => void;
}

function SliderRow({ label, param, min, max, step = 1, value, onChange }: SliderRowProps) {
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) =>
      onChange(param, parseFloat(e.target.value)),
    [param, onChange]
  );

  return (
    <div className="flex items-center gap-2 px-4 py-1 group">
      <span className="text-xs text-muted w-28 shrink-0">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        className="flex-1 accent-amber-400 cursor-pointer h-1"
      />
      <span className="text-xs font-mono text-muted w-10 text-right">
        {value > 0 ? `+${value}` : value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section header
// ---------------------------------------------------------------------------

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-3">
      <p className="text-[10px] uppercase tracking-widest text-muted/50 px-4 pb-1 border-b border-border/50">
        {title}
      </p>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EditPanel
// ---------------------------------------------------------------------------

/** Collapses the active edit stack into a flat parameter map for display. */
function collapseStack(stack: ReturnType<ReturnType<typeof useEditStore>["activeStack"]>): EditParameters {
  return stack.reduce<EditParameters>(
    (acc, edit) => ({ ...acc, ...edit.parameters }),
    {}
  );
}

const DEFAULT_PARAMS: Required<
  Pick<
    EditParameters,
    | "exposure" | "contrast" | "highlights" | "shadows"
    | "whites" | "blacks" | "clarity" | "texture"
    | "dehaze" | "vibrance" | "saturation"
    | "temperature" | "tint"
    | "sharpening_amount" | "noise_luminance" | "noise_color"
    | "vignette_amount"
  >
> = {
  exposure: 0, contrast: 0, highlights: 0, shadows: 0,
  whites: 0, blacks: 0, clarity: 0, texture: 0,
  dehaze: 0, vibrance: 0, saturation: 0,
  temperature: 0, tint: 0,
  sharpening_amount: 0, noise_luminance: 0, noise_color: 0,
  vignette_amount: 0,
};

export function EditPanel() {
  const { activeStack, pushEdit } = useEditStore();
  const params: EditParameters = useMemo(
    () => ({ ...DEFAULT_PARAMS, ...collapseStack(activeStack()) }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeStack()]
  );

  const handleChange = useCallback(
    (param: keyof EditParameters, value: number) => {
      pushEdit(
        `Adjust ${param}`,
        "parametric",
        `User adjusted ${param} to ${value}`,
        { [param]: value }
      );
    },
    [pushEdit]
  );

  const n = (key: keyof typeof DEFAULT_PARAMS) =>
    (params[key] as number) ?? 0;

  return (
    <div className="flex flex-col overflow-y-auto pb-8">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted px-4 py-3 border-b border-border">
        Adjustments
      </p>

      <Section title="Light">
        <SliderRow label="Exposure" param="exposure" min={-5} max={5} step={0.1} value={n("exposure")} onChange={handleChange} />
        <SliderRow label="Contrast" param="contrast" min={-100} max={100} value={n("contrast")} onChange={handleChange} />
        <SliderRow label="Highlights" param="highlights" min={-100} max={100} value={n("highlights")} onChange={handleChange} />
        <SliderRow label="Shadows" param="shadows" min={-100} max={100} value={n("shadows")} onChange={handleChange} />
        <SliderRow label="Whites" param="whites" min={-100} max={100} value={n("whites")} onChange={handleChange} />
        <SliderRow label="Blacks" param="blacks" min={-100} max={100} value={n("blacks")} onChange={handleChange} />
      </Section>

      <Section title="Presence">
        <SliderRow label="Clarity" param="clarity" min={-100} max={100} value={n("clarity")} onChange={handleChange} />
        <SliderRow label="Texture" param="texture" min={-100} max={100} value={n("texture")} onChange={handleChange} />
        <SliderRow label="Dehaze" param="dehaze" min={-100} max={100} value={n("dehaze")} onChange={handleChange} />
        <SliderRow label="Vibrance" param="vibrance" min={-100} max={100} value={n("vibrance")} onChange={handleChange} />
        <SliderRow label="Saturation" param="saturation" min={-100} max={100} value={n("saturation")} onChange={handleChange} />
      </Section>

      <Section title="White Balance">
        <SliderRow label="Temperature" param="temperature" min={-100} max={100} value={n("temperature")} onChange={handleChange} />
        <SliderRow label="Tint" param="tint" min={-150} max={150} value={n("tint")} onChange={handleChange} />
      </Section>

      <Section title="Detail">
        <SliderRow label="Sharpening" param="sharpening_amount" min={0} max={150} value={n("sharpening_amount")} onChange={handleChange} />
        <SliderRow label="Noise (Lum)" param="noise_luminance" min={0} max={100} value={n("noise_luminance")} onChange={handleChange} />
        <SliderRow label="Noise (Color)" param="noise_color" min={0} max={100} value={n("noise_color")} onChange={handleChange} />
      </Section>

      <Section title="Vignette">
        <SliderRow label="Amount" param="vignette_amount" min={-100} max={100} value={n("vignette_amount")} onChange={handleChange} />
      </Section>
    </div>
  );
}

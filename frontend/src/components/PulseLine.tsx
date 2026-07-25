interface PulseLineProps {
  active?: boolean;
}

/**
 * The product's signature visual: an ECG-style waveform that idles gently
 * and speeds up while an audit is in flight - a literal "pulse" for
 * Page Pulse.
 */
export function PulseLine({ active = false }: PulseLineProps) {
  return (
    <div className={`pulse-line-wrap${active ? " is-active" : ""}`} aria-hidden="true">
      <svg viewBox="0 0 420 40" preserveAspectRatio="none">
        <path
          className="pulse-line-path"
          d="M0 20 H130 L150 20 L162 6 L174 34 L186 20 L198 20 L210 20 H420"
        />
      </svg>
    </div>
  );
}

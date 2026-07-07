/**
 * TelemetryPulse — elemento firma de SALEMETRIQ.
 * Onda de osciloscopio que representa el "pulso" de una llamada: tramos de charla
 * (oscilación baja) y picos de momentos clave. Trazo con el gradiente-acento
 * violeta→cian y un barrido de señal sutil (se apaga con prefers-reduced-motion).
 */

// Path de telemetría: base plana + oscilaciones de conversación + 2 picos (momentos clave).
const PULSE_PATH =
  "M0,20 L18,20 22,14 26,26 30,20 44,20 48,10 52,30 56,20 70,20 " +
  "74,4 78,36 82,20 96,20 100,16 104,24 108,20 122,20 126,12 130,28 134,20 148,20";

export default function TelemetryPulse({
  className = "",
  height = 40,
  animated = true,
  strokeWidth = 2,
}) {
  return (
    <svg
      className={`smq-pulse ${animated ? "is-live" : ""} ${className}`}
      viewBox="0 0 148 40"
      height={height}
      width="100%"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="pulse-accent" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#7C3AED" />
          <stop offset="55%" stopColor="#8B5CF6" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <filter id="pulse-glow" x="-10%" y="-60%" width="120%" height="220%">
          <feGaussianBlur stdDeviation="1.6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path
        d={PULSE_PATH}
        fill="none"
        stroke="url(#pulse-accent)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#pulse-glow)"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

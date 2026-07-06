/**
 * Isotipo SALEMETRIQ — la "Q" como dial de medición, en dorado.
 */
export default function SalemetriqLogo({ size = 30, withWord = false, className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
        <defs>
          <linearGradient id="smq-gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#F6BC5E" />
            <stop offset="1" stopColor="#C9862A" />
          </linearGradient>
        </defs>
        <circle
          cx="50" cy="50" r="34" fill="none" stroke="url(#smq-gold)"
          strokeWidth="8" strokeLinecap="round"
          strokeDasharray="178 60" transform="rotate(126 50 50)"
        />
        <line x1="63" y1="63" x2="84" y2="84" stroke="url(#smq-gold)" strokeWidth="9" strokeLinecap="round" />
      </svg>
      {withWord && <span className="font-brand text-[14px] text-txt">SALEMETRIQ</span>}
    </div>
  );
}

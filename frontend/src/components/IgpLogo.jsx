/**
 * Isotipo IG PROSPECTOR — lupa de prospección sobre el marco de una cámara,
 * con el pulso violeta→cian de la IA (mismo lenguaje visual que el resto).
 */
export default function IgpLogo({ size = 30, withWord = false, className = "" }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
        <defs>
          <linearGradient id="igp-accent" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#8B5CF6" />
            <stop offset="1" stopColor="#22D3EE" />
          </linearGradient>
        </defs>
        {/* marco tipo cámara */}
        <rect x="14" y="14" width="72" height="72" rx="20" fill="none"
              stroke="url(#igp-accent)" strokeWidth="7" opacity="0.55" />
        {/* lupa (búsqueda) */}
        <circle cx="45" cy="45" r="17" fill="none" stroke="url(#igp-accent)" strokeWidth="8" />
        <line x1="58" y1="58" x2="78" y2="78" stroke="url(#igp-accent)" strokeWidth="9" strokeLinecap="round" />
      </svg>
      {withWord && <span className="font-brand text-[14px] text-txt">IG&nbsp;PROSPECTOR</span>}
    </div>
  );
}

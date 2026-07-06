import { Mic, Sparkles, Search } from "lucide-react";

/*
 * Call Analysis — análisis IA de un transcript (score, objeciones, sentiment, momentos clave).
 * Visual-first: layout de dos columnas + estado vacío. El motor IA se conecta en la Fase 3.
 */

const DIMENSIONES = [
  { k: "Apertura", d: "Rapport y encuadre" },
  { k: "Descubrimiento", d: "Preguntas y dolor" },
  { k: "Pitch", d: "Propuesta de valor" },
  { k: "Objeciones", d: "Manejo y resolución" },
  { k: "Cierre", d: "Pedido y próximos pasos" },
];

export default function CallAnalysis() {
  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">Análisis automático de cada llamada con IA: score, objeciones y momentos clave.</p>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
        {/* Selector de call */}
        <div className="card p-4 flex flex-col gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-txt-mute" />
            <input className="input pl-9" placeholder="Buscar llamada o closer…" />
          </div>
          <div className="flex flex-col items-center justify-center text-center py-14 px-4">
            <Mic size={22} className="text-txt-mute mb-3" />
            <p className="text-[13.5px] text-txt-mute">Elegí una llamada para ver su análisis.</p>
          </div>
        </div>

        {/* Panel de análisis */}
        <div className="card p-6">
          <div className="flex items-center gap-2 text-gold-400 mb-5">
            <Sparkles size={16} />
            <span className="text-[13px] font-semibold uppercase tracking-[0.12em]">Score por dimensión</span>
          </div>
          <div className="flex flex-col gap-4">
            {DIMENSIONES.map((dim) => (
              <div key={dim.k} className="flex items-center gap-4">
                <div className="w-40 shrink-0">
                  <div className="text-[14px] text-txt">{dim.k}</div>
                  <div className="text-[12px] text-txt-mute">{dim.d}</div>
                </div>
                <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden">
                  <div className="h-full rounded-full bg-ink-hover" style={{ width: "0%" }} />
                </div>
                <span className="text-[13px] text-txt-mute tnum w-10 text-right">—</span>
              </div>
            ))}
          </div>
          <p className="text-[13px] text-txt-mute mt-6 pt-5 border-t border-ink-line">
            El motor de análisis IA (score, objeciones detectadas, sentiment y transcript resaltado)
            se activa en la fase de datos.
          </p>
        </div>
      </div>
    </div>
  );
}

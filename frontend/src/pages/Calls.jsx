import { Phone, Upload, Filter } from "lucide-react";

/*
 * Calls — listado de llamadas de closers (transcripts).
 * Visual-first: estructura de tabla + estado vacío. Se cablea a /api/closers/:id/llamadas
 * y a la ingesta en la fase de datos.
 */

const COLS = ["Closer", "Lead", "Fecha", "Duración", "Resultado", "Valor"];

export default function Calls() {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <p className="text-[14px] text-txt-soft">Todas las llamadas cargadas, con su transcript y resultado.</p>
        <div className="flex items-center gap-2">
          <button className="btn-ghost flex items-center gap-2 border border-ink-line">
            <Filter size={16} /> Filtrar
          </button>
          <button className="btn-gold flex items-center gap-2 text-[14px]">
            <Upload size={16} /> Cargar transcript
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="grid grid-cols-6 gap-4 px-5 py-3 border-b border-ink-line">
          {COLS.map((c) => <span key={c} className="label">{c}</span>)}
        </div>
        <div className="flex flex-col items-center justify-center text-center py-20 px-6">
          <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
            <Phone size={22} className="text-txt-mute" />
          </div>
          <p className="text-txt font-medium">Todavía no hay llamadas cargadas</p>
          <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
            Subí un transcript manualmente o conectá la ingesta automática (n8n / webhook)
            para que las llamadas aparezcan acá.
          </p>
        </div>
      </div>
    </div>
  );
}

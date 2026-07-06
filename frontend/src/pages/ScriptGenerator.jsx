import { FileText, Sparkles, Wand2 } from "lucide-react";

/*
 * Script Generator — genera scripts/objeciones a medida a partir del contexto del equipo.
 * Visual-first: formulario + salida. La generación con IA se conecta en la Fase 3.
 */

const PLANTILLAS = [
  "Manejo de objeción de precio",
  "Apertura en frío",
  "Descubrimiento de dolor",
  "Cierre por urgencia",
];

export default function ScriptGenerator() {
  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">Generá scripts y respuestas a objeciones a medida del equipo, con IA.</p>

      <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-5">
        {/* Formulario */}
        <div className="card p-5 flex flex-col gap-4">
          <div>
            <label className="label">Tipo de script</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {PLANTILLAS.map((p) => (
                <button key={p} className="text-[12.5px] px-3 py-1.5 rounded-full border border-ink-line text-txt-soft hover:text-gold-400 hover:border-gold-500/40 transition-colors">
                  {p}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Contexto</label>
            <textarea
              className="input mt-2 h-32 resize-none"
              placeholder="Ej: producto SaaS de $2.500/mes, prospecto dueño de agencia, objeción principal de precio…"
            />
          </div>
          <button className="btn-gold flex items-center justify-center gap-2 text-[14px]">
            <Wand2 size={16} /> Generar script
          </button>
        </div>

        {/* Salida */}
        <div className="card p-6">
          <div className="flex items-center gap-2 text-gold-400 mb-5">
            <Sparkles size={16} />
            <span className="text-[13px] font-semibold uppercase tracking-[0.12em]">Script generado</span>
          </div>
          <div className="flex flex-col items-center justify-center text-center py-24 px-6">
            <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
              <FileText size={22} className="text-txt-mute" />
            </div>
            <p className="text-txt font-medium">Tu script va a aparecer acá</p>
            <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
              Elegí un tipo, agregá el contexto del prospecto y generá. La generación con IA
              se activa en la fase de datos.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

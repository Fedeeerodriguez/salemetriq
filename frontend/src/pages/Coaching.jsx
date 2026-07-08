import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { GraduationCap, AlertTriangle, ChevronRight } from "lucide-react";
import api from "../utils/api";

const ETAPA_LABEL = {
  cualificacion: "Cualificación",
  visualizacion: "Visualización",
  consecuencia: "Consecuencia (Miedo)",
  pitch: "Pitch",
  objeciones: "Objeciones",
  cierre: "Cierre",
};
const ORDEN = ["cualificacion", "visualizacion", "consecuencia", "pitch", "objeciones", "cierre"];

function barColor(v) {
  if (v == null) return "bg-ink-line";
  if (v < 40) return "bg-neg";
  if (v < 65) return "bg-gold-400";
  return "bg-pos";
}

/* Barras de promedio por etapa del método. */
export function EtapasBars({ etapas, debil }) {
  return (
    <div className="flex flex-col gap-2.5">
      {ORDEN.map((e) => {
        const v = etapas?.[e];
        return (
          <div key={e} className="flex items-center gap-3">
            <span className={`text-[12.5px] w-40 shrink-0 ${e === debil ? "text-neg font-medium" : "text-txt-soft"}`}>
              {ETAPA_LABEL[e]}{e === debil && " ⚠"}
            </span>
            <div className="flex-1 h-2 rounded-full bg-ink-raised overflow-hidden">
              <div className={`h-full rounded-full ${barColor(v)}`} style={{ width: `${v ?? 0}%` }} />
            </div>
            <span className="text-[12.5px] tnum w-9 text-right text-txt">{v ?? "—"}</span>
          </div>
        );
      })}
    </div>
  );
}

/* Adopción de técnicas del método (menos usadas primero = mayores fugas). */
export function ChecklistAdopcion({ checklist }) {
  if (!checklist?.length) return <div className="text-[13px] text-txt-mute">Sin datos suficientes todavía.</div>;
  return (
    <div className="flex flex-col gap-2">
      {checklist.map((c) => (
        <div key={c.key} className="flex items-center gap-3">
          <span className="text-[12.5px] flex-1 text-txt-soft truncate">{c.label}</span>
          <div className="w-28 h-1.5 rounded-full bg-ink-raised overflow-hidden">
            <div className={`h-full ${c.pct < 40 ? "bg-neg" : c.pct < 70 ? "bg-gold-400" : "bg-pos"}`} style={{ width: `${c.pct}%` }} />
          </div>
          <span className="text-[12px] tnum w-9 text-right text-txt-mute">{c.pct}%</span>
        </div>
      ))}
    </div>
  );
}

function Narrativa({ texto }) {
  if (!texto) return null;
  return (
    <div className="card liquid p-5">
      <div className="flex items-center gap-2 mb-2 text-accent">
        <GraduationCap size={16} />
        <span className="label text-accent">Diagnóstico del equipo</span>
      </div>
      <div className="text-[13.5px] text-txt-soft whitespace-pre-wrap leading-relaxed">{texto}</div>
    </div>
  );
}

export default function Coaching() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/coaching/equipo").then((r) => setData(r.data)).catch(() => setErr("No se pudo cargar el coaching."));
  }, []);

  if (err) return <div className="card p-5 text-[14px] text-neg">{err}</div>;
  if (!data) return <div className="card p-5 text-[14px] text-txt-mute">Cargando coaching…</div>;
  if (!data.n) return <div className="card p-5 text-[14px] text-txt-mute">Todavía no hay llamadas analizadas. Cuando entren y se analicen, acá vas a ver dónde mejora el equipo.</div>;

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">
        Análisis de {data.n} llamada(s) contra el método. Score promedio del equipo:{" "}
        <span className="text-txt font-medium">{data.score_prom ?? "—"}</span>.
      </p>

      <Narrativa texto={data.narrativa} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="label mb-4">Promedio por etapa del método</div>
          <EtapasBars etapas={data.etapas_prom} debil={data.etapa_debil} />
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle size={14} className="text-gold-400" />
            <span className="label">Dónde falla el método (adopción de técnicas)</span>
          </div>
          <ChecklistAdopcion checklist={data.checklist} />
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-white/[0.06] label">Ranking de closers</div>
        {data.ranking?.length ? data.ranking.map((c, i) => (
          <Link key={c.closer_id} to={`/users/${c.closer_id}`}
                className="grid grid-cols-[auto_1fr_auto_auto_auto] gap-4 items-center px-5 py-3 border-b border-white/[0.05] last:border-0 hover:bg-ink-hover transition-colors">
            <span className="text-[13px] text-txt-mute tnum w-5">{i + 1}</span>
            <span className="text-[14px] text-txt truncate">{c.nombre}</span>
            <span className="text-[12.5px] text-txt-mute tnum">{c.llamadas} llam.</span>
            <span className="font-display text-[15px] font-semibold tnum w-10 text-right text-txt">{c.score_prom}</span>
            <ChevronRight size={15} className="text-txt-mute" />
          </Link>
        )) : <div className="px-5 py-8 text-center text-[13px] text-txt-mute">Sin datos.</div>}
      </div>
    </div>
  );
}

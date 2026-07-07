import { useEffect, useState } from "react";
import { Phone, Upload, Filter } from "lucide-react";
import api from "../utils/api";

/*
 * Calls — listado global de llamadas de closers, con datos reales de /api/calls.
 */

const COLS = ["Closer", "Lead", "Fecha", "Duración", "Resultado", "Valor"];

const OUTCOME = {
  cerro:       { label: "Cerró", cls: "pill-pos" },
  no_cerro:    { label: "No cerró", cls: "pill-neg" },
  seguimiento: { label: "Seguimiento", cls: "pill text-iris-400 bg-iris-500/12" },
  no_show:     { label: "No show", cls: "pill text-txt-mute bg-white/[0.05]" },
};

const money = (n) => "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });
const dur = (s) => (s ? `${Math.round(s / 60)} min` : "—");
const fecha = (f) =>
  f ? new Date(f).toLocaleDateString("es-AR", { day: "2-digit", month: "short" }) : "—";

function Badge({ outcome }) {
  const o = OUTCOME[outcome] || { label: outcome || "—", cls: "pill text-txt-mute bg-white/[0.05]" };
  const cls = o.cls.startsWith("pill") ? o.cls : `pill ${o.cls}`;
  return <span className={cls}>{o.label}</span>;
}

export default function Calls() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get("/calls")
      .then((r) => setCalls(r.data))
      .catch(() => setErr("No se pudieron cargar las llamadas."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <p className="text-[14px] text-txt-soft">
          {loading ? "Cargando llamadas…" : `${calls.length} llamadas con su transcript y resultado.`}
        </p>
        <div className="flex items-center gap-2">
          <button className="btn-ghost flex items-center gap-2 border border-ink-line">
            <Filter size={16} /> Filtrar
          </button>
          <button className="btn-primary flex items-center gap-2 text-[14px]">
            <Upload size={16} /> Cargar transcript
          </button>
        </div>
      </div>

      {err && <div className="card p-4 text-[13.5px] text-txt-soft">{err}</div>}

      <div className="card overflow-hidden">
        <div className="grid grid-cols-[1.2fr_1.2fr_auto_auto_auto_auto] gap-4 px-5 py-3 border-b border-white/[0.06]">
          {COLS.map((c, i) => (
            <span key={c} className={`label ${i >= 3 ? "text-right" : ""}`}>{c}</span>
          ))}
        </div>

        {!loading && calls.length === 0 && !err && (
          <div className="flex flex-col items-center justify-center text-center py-20 px-6">
            <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
              <Phone size={22} className="text-txt-mute" />
            </div>
            <p className="text-txt font-medium">Todavía no hay llamadas cargadas</p>
            <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
              Subí un transcript o conectá la ingesta automática para que aparezcan acá.
            </p>
          </div>
        )}

        {calls.map((c) => (
          <div
            key={c.id}
            className="grid grid-cols-[1.2fr_1.2fr_auto_auto_auto_auto] gap-4 items-center px-5 py-3.5 border-b border-white/[0.05] last:border-0 hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-[14px] text-txt truncate">{c.closer_nombre || "—"}</span>
            <span className="text-[13.5px] text-txt-soft truncate">{c.lead_nombre || "—"}</span>
            <span className="text-[13.5px] text-txt-soft tnum text-right">{fecha(c.fecha)}</span>
            <span className="text-[13.5px] text-txt-soft tnum text-right">{dur(c.duracion_seg)}</span>
            <span className="text-right"><Badge outcome={c.outcome} /></span>
            <span className="font-display text-[14px] tnum text-right text-gold-400">
              {c.outcome === "cerro" ? money(c.deal_value) : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

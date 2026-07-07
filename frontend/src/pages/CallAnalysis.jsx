import { useEffect, useState } from "react";
import { Mic, Sparkles, Search, Clock, User } from "lucide-react";
import api from "../utils/api";
import TelemetryPulse from "../components/TelemetryPulse";
import CallDrawer from "../components/CallDrawer";

/*
 * Call Analysis — grabaciones de llamadas como tarjetas (datos reales de
 * /api/recordings). Cada tarjeta muestra el score IA y el sentiment. El drawer
 * lateral tipo Notion + fullscreen se suma en la Fase C.
 */

const dur = (s) => (s ? `${Math.round(s / 60)} min` : "—");
const fecha = (f) =>
  f ? new Date(f).toLocaleDateString("es-AR", { day: "2-digit", month: "short" }) : "—";

const SENT = {
  positivo: "pill-pos",
  neutral: "pill text-iris-400 bg-iris-500/12",
  negativo: "pill-neg",
};

function scoreColor(n) {
  if (n >= 75) return "text-pos";
  if (n >= 60) return "text-gold-400";
  return "text-neg";
}

function Card({ rec, active, onClick }) {
  const closer = (rec.participants || []).find((p) => p.rol === "closer");
  const prospecto = (rec.participants || []).find((p) => p.rol === "prospecto");
  return (
    <button
      onClick={onClick}
      className={`card p-4 text-left flex flex-col gap-3 transition-shadow hover:shadow-glow ${
        active ? "ring-1 ring-iris-500/50" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[14px] font-medium text-txt truncate">{rec.title || "Llamada"}</div>
          <div className="flex items-center gap-1.5 mt-1 text-[12px] text-txt-mute">
            <User size={12} /> {closer?.nombre || "—"}
          </div>
        </div>
        {rec.score != null ? (
          <div className="text-right shrink-0">
            <div className={`font-display text-[22px] font-semibold tnum leading-none ${scoreColor(rec.score)}`}>
              {Math.round(rec.score)}
            </div>
            <div className="text-[10px] uppercase tracking-wider text-txt-mute mt-0.5">score</div>
          </div>
        ) : (
          <span className="pill text-txt-mute bg-white/[0.05] shrink-0">Sin analizar</span>
        )}
      </div>

      <TelemetryPulse height={26} animated={active} />

      <div className="flex items-center justify-between text-[12px] text-txt-mute">
        <span className="flex items-center gap-1.5"><Clock size={12} /> {dur(rec.duration_seg)} · {fecha(rec.recorded_at)}</span>
        {rec.sentiment && <span className={SENT[rec.sentiment] || "pill"}>{rec.sentiment}</span>}
      </div>
      {prospecto && <div className="text-[12px] text-txt-soft truncate">Prospecto: {prospecto.nombre}</div>}
    </button>
  );
}

export default function CallAnalysis() {
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [activeId, setActiveId] = useState(null);

  useEffect(() => {
    api.get("/recordings").then((r) => setRecs(r.data)).catch(() => setRecs([])).finally(() => setLoading(false));
  }, []);

  const filtered = recs.filter((r) => (r.title || "").toLowerCase().includes(q.toLowerCase()));
  const analizadas = recs.filter((r) => r.score != null).length;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-4">
        <p className="text-[14px] text-txt-soft">
          {loading ? "Cargando grabaciones…" : `${recs.length} grabaciones · ${analizadas} analizadas con IA`}
        </p>
        <div className="relative w-64 max-w-full">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-txt-mute" />
          <input
            className="input pl-9"
            placeholder="Buscar grabación…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      {!loading && recs.length === 0 && (
        <div className="card flex flex-col items-center justify-center text-center py-20 px-6">
          <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
            <Mic size={22} className="text-txt-mute" />
          </div>
          <p className="text-txt font-medium">Todavía no hay grabaciones</p>
          <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
            Conectá Fathom (u otra herramienta) para que los transcripts lleguen acá y se analicen.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((rec) => (
          <Card key={rec.id} rec={rec} active={activeId === rec.id} onClick={() => setActiveId(rec.id)} />
        ))}
      </div>

      {recs.length > 0 && (
        <div className="flex items-center gap-2 text-[13px] text-txt-mute">
          <Sparkles size={14} className="text-iris-400" />
          Clic en una tarjeta para abrir el análisis completo. Botón de pantalla completa dentro del panel.
        </div>
      )}

      {activeId && <CallDrawer recId={activeId} onClose={() => setActiveId(null)} />}
    </div>
  );
}

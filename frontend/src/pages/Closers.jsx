import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import api from "../utils/api";

/*
 * Closers — equipo de cierre con su performance.
 * Lista real desde /api/closers; las métricas por closer se suman en la fase de datos.
 */
export default function Closers() {
  const [closers, setClosers] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/closers")
      .then((r) => setClosers(r.data))
      .catch(() => setErr("No se pudieron cargar los closers."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">Equipo de cierre y su performance por período.</p>

      {err && <div className="card p-4 text-[13.5px] text-txt-soft">{err}</div>}

      <div className="card overflow-hidden">
        <div className="grid grid-cols-[1fr_auto_auto] gap-4 px-5 py-3 border-b border-ink-line">
          <span className="label">Closer</span>
          <span className="label">Close rate</span>
          <span className="label">Rol</span>
        </div>

        {loading && <div className="px-5 py-8 text-[13.5px] text-txt-mute">Cargando…</div>}

        {!loading && closers.length === 0 && !err && (
          <div className="flex flex-col items-center justify-center text-center py-20 px-6">
            <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
              <Users size={22} className="text-txt-mute" />
            </div>
            <p className="text-txt font-medium">Todavía no hay closers cargados</p>
            <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
              Agregá miembros del equipo con rol <span className="text-gold-400">closer</span> para
              verlos rankeados acá.
            </p>
          </div>
        )}

        {closers.map((c) => (
          <div key={c.id} className="grid grid-cols-[1fr_auto_auto] gap-4 items-center px-5 py-3.5 border-b border-ink-line last:border-0">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-gold-500/15 text-gold-400 grid place-items-center text-[12px] font-semibold shrink-0">
                {(c.nombre || c.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-[14px] text-txt truncate">{c.nombre || c.email}</div>
                <div className="text-[12px] text-txt-mute truncate">{c.email}</div>
              </div>
            </div>
            <span className="text-[14px] text-txt-soft tnum">—</span>
            <span className="pill text-gold-400 bg-gold-500/10">closer</span>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Users } from "lucide-react";
import api from "../utils/api";

const money = (n) =>
  "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });

/*
 * Closers — equipo de cierre rankeado por close rate, con métricas reales.
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

  const maxRate = Math.max(1, ...closers.map((c) => c.close_rate || 0));

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">Equipo de cierre rankeado por close rate del período.</p>

      {err && <div className="card p-4 text-[13.5px] text-txt-soft">{err}</div>}

      <div className="card overflow-hidden">
        <div className="grid grid-cols-[1.4fr_1.3fr_auto_auto] gap-4 px-5 py-3 border-b border-white/[0.06]">
          <span className="label">Closer</span>
          <span className="label">Close rate</span>
          <span className="label text-right">Llamadas</span>
          <span className="label text-right">Facturación</span>
        </div>

        {loading && <div className="px-5 py-8 text-[13.5px] text-txt-mute">Cargando…</div>}

        {!loading && closers.length === 0 && !err && (
          <div className="flex flex-col items-center justify-center text-center py-20 px-6">
            <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
              <Users size={22} className="text-txt-mute" />
            </div>
            <p className="text-txt font-medium">Todavía no hay closers cargados</p>
            <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
              Agregá miembros del equipo con rol <span className="text-iris-400">closer</span> para
              verlos rankeados acá.
            </p>
          </div>
        )}

        {closers.map((c, i) => (
          <Link
            to={`/users/${c.id}`}
            key={c.id}
            className="grid grid-cols-[1.4fr_1.3fr_auto_auto] gap-4 items-center px-5 py-3.5 border-b border-white/[0.05] last:border-0 hover:bg-white/[0.03] transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-[12px] text-txt-mute tnum w-4 shrink-0">{i + 1}</span>
              <div className="w-8 h-8 rounded-full bg-iris-500/20 text-iris-400 grid place-items-center text-[12px] font-semibold shrink-0 ring-1 ring-iris-500/30">
                {(c.nombre || c.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-[14px] text-txt truncate">{c.nombre || c.email}</div>
                <div className="text-[12px] text-txt-mute truncate">
                  {c.cerradas}/{c.llamadas} cerradas
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 min-w-0">
              <div className="flex-1 h-1.5 rounded-full bg-ink-line overflow-hidden max-w-[140px]">
                <div
                  className="h-full rounded-full bg-accent-grad"
                  style={{ width: `${((c.close_rate || 0) / maxRate) * 100}%` }}
                />
              </div>
              <span className="font-display text-[14px] text-txt tnum">{c.close_rate}%</span>
            </div>

            <span className="text-[14px] text-txt-soft tnum text-right">{c.llamadas}</span>
            <span className="font-display text-[14px] text-gold-400 tnum text-right">{money(c.revenue)}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

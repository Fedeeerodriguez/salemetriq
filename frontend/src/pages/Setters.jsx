import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Headphones, ChevronRight } from "lucide-react";
import api from "../utils/api";

/*
 * Setters — equipo de setting. Click en un setter → su perfil con set rate,
 * calidad de leads y timeline de resúmenes.
 */
export default function Setters() {
  const [setters, setSetters] = useState([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/setters")
      .then((r) => setSetters(r.data))
      .catch(() => setErr("No se pudieron cargar los setters."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-5">
      <p className="text-[14px] text-txt-soft">Equipo de setting. Entrá a un setter para ver su performance.</p>

      {err && <div className="card p-4 text-[13.5px] text-txt-soft">{err}</div>}

      <div className="card overflow-hidden">
        <div className="grid grid-cols-[1fr_auto] gap-4 px-5 py-3 border-b border-white/[0.06]">
          <span className="label">Setter</span>
          <span className="label">Perfil</span>
        </div>

        {loading && <div className="px-5 py-8 text-[13.5px] text-txt-mute">Cargando…</div>}

        {!loading && setters.length === 0 && !err && (
          <div className="flex flex-col items-center justify-center text-center py-20 px-6">
            <div className="w-12 h-12 rounded-xl bg-ink-raised grid place-items-center mb-4">
              <Headphones size={22} className="text-txt-mute" />
            </div>
            <p className="text-txt font-medium">Todavía no hay setters cargados</p>
            <p className="text-[13.5px] text-txt-mute mt-1 max-w-sm">
              Agregá miembros con rol <span className="text-iris-400">setter</span> para verlos acá.
            </p>
          </div>
        )}

        {setters.map((s) => (
          <Link
            to={`/users/${s.id}`}
            key={s.id}
            className="grid grid-cols-[1fr_auto] gap-4 items-center px-5 py-3.5 border-b border-white/[0.05] last:border-0 hover:bg-white/[0.03] transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-400 grid place-items-center text-[12px] font-semibold shrink-0 ring-1 ring-cyan-500/30">
                {(s.nombre || s.email || "?").slice(0, 1).toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="text-[14px] text-txt truncate">{s.nombre || s.email}</div>
                <div className="text-[12px] text-txt-mute truncate">{s.email}</div>
              </div>
            </div>
            <ChevronRight size={18} className="text-txt-mute" />
          </Link>
        ))}
      </div>
    </div>
  );
}

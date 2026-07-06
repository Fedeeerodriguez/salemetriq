import { useEffect, useState } from "react";
import { PhoneCall } from "lucide-react";
import api from "../utils/api";

export default function Closers() {
  const [closers, setClosers] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get("/closers")
      .then((r) => setClosers(r.data))
      .catch(() => setErr("No se pudieron cargar los closers."));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <PhoneCall className="text-pulse-300" size={22} />
        <div>
          <h1 className="text-2xl font-semibold text-[#EAF2F3]">Closers</h1>
          <p className="text-sm text-[#6C7B84]">Análisis de llamadas y performance de cierre.</p>
        </div>
      </div>

      {err && <div className="card p-4 text-sm text-[#8B949E]">{err}</div>}

      <div className="card divide-y divide-surface-border">
        {closers.length === 0 && !err && (
          <div className="p-6 text-sm text-[#6C7B84]">Todavía no hay closers cargados.</div>
        )}
        {closers.map((c) => (
          <div key={c.id} className="flex items-center justify-between px-5 py-3">
            <div>
              <div className="text-[#EAF2F3]">{c.nombre || c.email}</div>
              <div className="text-xs text-[#6C7B84]">{c.email}</div>
            </div>
            <span className="badge bg-pulse-400/10 text-pulse-300">closer</span>
          </div>
        ))}
      </div>
    </div>
  );
}

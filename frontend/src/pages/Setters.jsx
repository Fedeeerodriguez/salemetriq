import { useEffect, useState } from "react";
import { Headphones } from "lucide-react";
import api from "../utils/api";

export default function Setters() {
  const [setters, setSetters] = useState([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get("/setters")
      .then((r) => setSetters(r.data))
      .catch(() => setErr("No se pudieron cargar los setters."));
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Headphones className="text-champ" size={22} />
        <div>
          <h1 className="text-2xl font-semibold text-[#EAF2F3]">Setters</h1>
          <p className="text-sm text-[#6C7B84]">Resúmenes por audio y texto — calidad de agenda.</p>
        </div>
      </div>

      {err && <div className="card p-4 text-sm text-[#8B949E]">{err}</div>}

      <div className="card divide-y divide-surface-border">
        {setters.length === 0 && !err && (
          <div className="p-6 text-sm text-[#6C7B84]">Todavía no hay setters cargados.</div>
        )}
        {setters.map((s) => (
          <div key={s.id} className="flex items-center justify-between px-5 py-3">
            <div>
              <div className="text-[#EAF2F3]">{s.nombre || s.email}</div>
              <div className="text-xs text-[#6C7B84]">{s.email}</div>
            </div>
            <span className="badge bg-champ/10 text-champ">setter</span>
          </div>
        ))}
      </div>
    </div>
  );
}

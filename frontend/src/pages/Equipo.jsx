import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Shield, Phone, Headphones, Bot, Star, Building2 } from "lucide-react";
import api from "../utils/api";
import { getWorkspace } from "../utils/auth";

const ROL = {
  admin: { icon: Shield, strip: "bg-iris-500", ring: "ring-iris-500/30", tint: "bg-iris-500/20 text-iris-400", label: "Admin" },
  closer: { icon: Phone, strip: "bg-gold-400", ring: "ring-gold-400/30", tint: "bg-gold-400/20 text-gold-400", label: "Closer" },
  setter: { icon: Headphones, strip: "bg-cyan-500", ring: "ring-cyan-500/30", tint: "bg-cyan-500/20 text-cyan-400", label: "Setter" },
};

/* Tarjeta estilo "paperclip": pestaña de color arriba (el clip), avatar centrado,
   y al hover sube un overlay con las métricas. */
function PersonCard({ m }) {
  const r = ROL[m.rol] || ROL.admin;
  const Icon = r.icon;
  return (
    <Link to={`/users/${m.id}`} className="group relative block">
      <div className="card overflow-hidden transition-transform duration-200 group-hover:-translate-y-1 group-hover:shadow-glow">
        <div className={`h-1.5 ${r.strip}`} />
        <div className="p-4 pb-5 flex flex-col items-center text-center gap-2">
          <div className={`w-12 h-12 rounded-2xl grid place-items-center text-[16px] font-display font-semibold ring-1 ${r.tint} ${r.ring}`}>
            {(m.nombre || m.email || "?").slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 w-full">
            <div className="text-[14px] font-medium text-txt truncate flex items-center justify-center gap-1">
              {m.nombre || m.email}
              {m.es_owner && <Star size={12} className="text-gold-400 shrink-0" title="Dueño del workspace" />}
            </div>
            <span className={`pill ${r.tint} inline-flex items-center gap-1 mt-1`}><Icon size={10} /> {r.label}</span>
          </div>
        </div>
        {/* overlay de métricas (hover) */}
        <div className="absolute inset-x-0 bottom-0 translate-y-full group-hover:translate-y-0 transition-transform duration-200 bg-ink-raised/95 backdrop-blur-sm border-t border-white/[0.06] px-4 py-2.5 flex items-center justify-around">
          {m.kpis.map((k) => (
            <div key={k.label} className="text-center">
              <div className="font-display text-[14px] font-semibold text-txt tnum">{k.value}</div>
              <div className="text-[10px] text-txt-mute uppercase tracking-wide">{k.label}</div>
            </div>
          ))}
        </div>
      </div>
    </Link>
  );
}

function AgentCard({ a }) {
  return (
    <div className="group relative">
      <div className="card overflow-hidden transition-transform duration-200 group-hover:-translate-y-1 group-hover:shadow-glow">
        <div className="h-1.5 bg-accent-grad" />
        <div className="p-4 pb-5 flex flex-col items-center text-center gap-2">
          <div className="w-12 h-12 rounded-2xl grid place-items-center ring-1 ring-iris-500/30" style={{ background: "linear-gradient(135deg, rgba(124,58,237,0.25), rgba(34,211,238,0.2))" }}>
            <Bot size={20} className="text-iris-300" />
          </div>
          <div className="min-w-0 w-full">
            <div className="text-[14px] font-medium text-txt truncate">{a.nombre}</div>
            <span className="pill text-accent bg-iris-500/12 inline-flex items-center gap-1 mt-1">agente IA</span>
          </div>
          <p className="text-[11.5px] text-txt-mute leading-snug">{a.descripcion}</p>
        </div>
        <div className="absolute inset-x-0 bottom-0 translate-y-full group-hover:translate-y-0 transition-transform duration-200 bg-ink-raised/95 backdrop-blur-sm border-t border-white/[0.06] px-4 py-2.5 flex items-center justify-around">
          {a.kpis.map((k) => (
            <div key={k.label} className="text-center">
              <div className="font-display text-[14px] font-semibold text-txt tnum">{k.value}</div>
              <div className="text-[10px] text-txt-mute uppercase tracking-wide">{k.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Column({ label, count, accent, children }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 justify-center">
        <span className={`w-1.5 h-1.5 rounded-full ${accent}`} />
        <span className="label">{label}</span>
        <span className="text-[11px] text-txt-mute tnum">{count}</span>
      </div>
      <div className="flex flex-col gap-3">{children}</div>
    </div>
  );
}

export default function Equipo() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/workspace/equipo").then((r) => setData(r.data)).catch(() => setErr("No se pudo cargar el equipo."));
  }, []);

  if (err) return <div className="card p-5 text-[14px] text-neg">{err}</div>;
  if (!data) return <div className="card p-5 text-[14px] text-txt-mute">Cargando equipo…</div>;

  const accents = { admin: "bg-iris-500", closer: "bg-gold-400", setter: "bg-cyan-500" };

  return (
    <div className="flex flex-col items-center gap-6">
      <p className="text-[14px] text-txt-soft self-start">
        Organigrama de tu workspace. Pasá el mouse por una tarjeta para ver métricas; hacé clic para abrir el perfil.
      </p>

      {/* Nodo raíz: el workspace */}
      <div className="card liquid px-6 py-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-iris-500/20 text-iris-400 grid place-items-center ring-1 ring-iris-500/30">
          <Building2 size={19} />
        </div>
        <div>
          <div className="font-display text-[16px] font-semibold text-txt">{data.workspace || getWorkspace()}</div>
          <div className="text-[12px] text-txt-mute">Workspace</div>
        </div>
      </div>

      <div className="w-px h-5 bg-ink-line" />

      {/* Columnas por rol + agentes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full items-start">
        {data.grupos.map((g) => (
          <Column key={g.rol} label={g.label} count={g.miembros.length} accent={accents[g.rol]}>
            {g.miembros.map((m) => <PersonCard key={m.id} m={m} />)}
          </Column>
        ))}
        {data.agentes?.length > 0 && (
          <Column label="Agentes IA" count={data.agentes.length} accent="bg-accent-grad">
            {data.agentes.map((a) => <AgentCard key={a.nombre} a={a} />)}
          </Column>
        )}
      </div>
    </div>
  );
}

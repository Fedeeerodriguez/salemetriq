import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Loader2, CheckCircle2, XCircle, Hash, AtSign, Type, MapPin } from "lucide-react";
import api from "../../utils/api";

const ANGULOS = [
  { id: "hashtag", label: "Hashtag", icon: Hash, ph: "medicos" },
  { id: "keyword", label: "Keyword", icon: Type, ph: "cardiólogo" },
  { id: "followers", label: "Seguidores de @", icon: AtSign, ph: "sociedadcardiologia" },
  { id: "ubicacion", label: "Ubicación", icon: MapPin, ph: "Santa Rosa La Pampa" },
];

export default function Buscar() {
  const navigate = useNavigate();
  const [nichos, setNichos] = useState([]);
  const [nichoId, setNichoId] = useState("");
  const [angulo, setAngulo] = useState("hashtag");
  const [query, setQuery] = useState("");
  const [filtros, setFiltros] = useState({ limite: 50, min_followers: "", max_followers: "", solo_business: false, con_contacto: false, min_score: "" });
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const poll = useRef(null);

  useEffect(() => {
    api.get("/igp/nichos").then(({ data }) => setNichos(data)).catch(() => {});
    return () => clearInterval(poll.current);
  }, []);

  useEffect(() => {
    const n = nichos.find((x) => x.id === nichoId);
    if (n && angulo === "hashtag" && n.hashtags?.length) setQuery(n.hashtags[0]);
    if (n && angulo === "followers" && n.cuentas_semilla?.length) setQuery(n.cuentas_semilla[0]);
  }, [nichoId, angulo]); // eslint-disable-line

  function limpiarFiltros() {
    const f = { ...filtros };
    const out = { limite: Number(f.limite) || 50 };
    if (f.min_followers) out.min_followers = Number(f.min_followers);
    if (f.max_followers) out.max_followers = Number(f.max_followers);
    if (f.min_score) out.min_score = Number(f.min_score);
    if (f.solo_business) out.solo_business = true;
    if (f.con_contacto) out.con_contacto = true;
    return out;
  }

  async function lanzar(e) {
    e.preventDefault();
    setError(""); setJob(null);
    clearInterval(poll.current);
    try {
      const { data } = await api.post("/igp/busqueda", {
        angulo, query, nicho_id: nichoId || null, filtros: limpiarFiltros(),
      });
      setJob(data);
      poll.current = setInterval(async () => {
        const { data: j } = await api.get(`/igp/busqueda/${data.id}`);
        setJob(j);
        if (j.estado === "ok" || j.estado === "error") clearInterval(poll.current);
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo lanzar la búsqueda");
    }
  }

  const corriendo = job && (job.estado === "pendiente" || job.estado === "corriendo");
  const AnguloIcon = ANGULOS.find((a) => a.id === angulo)?.icon || Hash;

  return (
    <div className="max-w-3xl">
      <p className="text-txt-soft text-sm mb-6">
        Elegí un <b className="text-txt">nicho</b> y un <b className="text-txt">ángulo</b>, y traemos perfiles reales,
        deduplicados y puntuados por afinidad. Después los mandás a una lista.
      </p>

      <form onSubmit={lanzar} className="card p-5 flex flex-col gap-4">
        {/* Nicho */}
        <div>
          <label className="label">Nicho</label>
          <select className="input mt-1.5" value={nichoId} onChange={(e) => setNichoId(e.target.value)}>
            <option value="">— Sin nicho (búsqueda libre) —</option>
            {nichos.map((n) => <option key={n.id} value={n.id}>{n.nombre}</option>)}
          </select>
        </div>

        {/* Ángulo */}
        <div>
          <label className="label">Ángulo</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-1.5">
            {ANGULOS.map((a) => {
              const Icon = a.icon;
              const active = angulo === a.id;
              return (
                <button key={a.id} type="button" onClick={() => setAngulo(a.id)}
                  className={`flex items-center gap-2 justify-center rounded-lg px-3 py-2.5 text-[13px] font-medium border transition-colors ${
                    active ? "border-iris-500 bg-iris-500/10 text-txt" : "border-ink-line text-txt-soft hover:text-txt hover:bg-ink-hover"
                  }`}>
                  <Icon size={15} /> {a.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Query */}
        <div>
          <label className="label">{angulo === "followers" ? "Cuenta (@usuario)" : angulo === "hashtag" ? "Hashtag (sin #)" : "Término"}</label>
          <div className="relative mt-1.5">
            <AnguloIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-txt-mute" />
            <input className="input pl-9" required value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder={ANGULOS.find((a) => a.id === angulo)?.ph} />
          </div>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label className="label">Límite</label>
            <input type="number" className="input mt-1.5" value={filtros.limite}
              onChange={(e) => setFiltros({ ...filtros, limite: e.target.value })} />
          </div>
          <div>
            <label className="label">Seg. mín</label>
            <input type="number" className="input mt-1.5" value={filtros.min_followers}
              onChange={(e) => setFiltros({ ...filtros, min_followers: e.target.value })} />
          </div>
          <div>
            <label className="label">Seg. máx</label>
            <input type="number" className="input mt-1.5" value={filtros.max_followers}
              onChange={(e) => setFiltros({ ...filtros, max_followers: e.target.value })} />
          </div>
          <div>
            <label className="label">Score mín</label>
            <input type="number" className="input mt-1.5" value={filtros.min_score}
              onChange={(e) => setFiltros({ ...filtros, min_score: e.target.value })} />
          </div>
        </div>
        <div className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-[13px] text-txt-soft cursor-pointer">
            <input type="checkbox" checked={filtros.solo_business}
              onChange={(e) => setFiltros({ ...filtros, solo_business: e.target.checked })} /> Solo cuentas profesionales
          </label>
          <label className="flex items-center gap-2 text-[13px] text-txt-soft cursor-pointer">
            <input type="checkbox" checked={filtros.con_contacto}
              onChange={(e) => setFiltros({ ...filtros, con_contacto: e.target.checked })} /> Con email o web
          </label>
        </div>

        {error && <div className="text-[13.5px] text-neg">{error}</div>}
        <button className="btn-primary flex items-center justify-center gap-2" disabled={corriendo}>
          <Search size={16} /> {corriendo ? "Buscando…" : "Buscar"}
        </button>
      </form>

      {/* Estado del job */}
      {job && (
        <div className="card p-4 mt-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {corriendo && <Loader2 size={20} className="text-iris-400 animate-spin" />}
            {job.estado === "ok" && <CheckCircle2 size={20} className="text-pos" />}
            {job.estado === "error" && <XCircle size={20} className="text-neg" />}
            <div>
              <div className="text-[14px] font-medium text-txt capitalize">{job.estado}</div>
              <div className="text-[12.5px] text-txt-soft">
                {job.estado === "ok"
                  ? `${job.total_encontrados} perfiles (${job.total_nuevos} nuevos)`
                  : job.estado === "error" ? (job.error_msg || "Error") : "Trayendo perfiles…"}
              </div>
            </div>
          </div>
          {job.estado === "ok" && (
            <button onClick={() => navigate(`/prospeccion/perfiles${nichoId ? `?nicho=${nichoId}` : ""}`)} className="btn-ghost">
              Ver perfiles →
            </button>
          )}
        </div>
      )}
    </div>
  );
}

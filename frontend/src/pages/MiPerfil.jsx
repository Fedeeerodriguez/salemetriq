import { useState } from "react";
import { User, Mail, Shield, Lock, Check, Loader2, Plug } from "lucide-react";
import { getUser, updateMe } from "../utils/auth";
import Conexiones from "./Conexiones";

const ROL_LABEL = { admin: "Owner", closer: "Closer", setter: "Setter", superadmin: "Plataforma" };

export default function MiPerfil() {
  const [me, setMe] = useState(getUser());
  const [nombre, setNombre] = useState(me?.nombre || "");
  const [pActual, setPActual] = useState("");
  const [pNueva, setPNueva] = useState("");
  const [pRepite, setPRepite] = useState("");
  const [busy, setBusy] = useState(false);
  const [ok, setOk] = useState("");
  const [err, setErr] = useState("");

  const rol = me?.is_superadmin ? "superadmin" : me?.rol;
  const inicial = (me?.nombre || me?.email || "U").slice(0, 1).toUpperCase();
  const cambiaPass = Boolean(pNueva || pActual || pRepite);

  async function guardar(e) {
    e.preventDefault();
    setErr(""); setOk("");

    if (cambiaPass) {
      if (pNueva.length < 6) return setErr("La contraseña nueva debe tener al menos 6 caracteres.");
      if (pNueva !== pRepite) return setErr("Las contraseñas nuevas no coinciden.");
      if (!pActual) return setErr("Ingresá tu contraseña actual.");
    }

    const payload = {};
    if (nombre.trim() && nombre.trim() !== (me?.nombre || "")) payload.nombre = nombre.trim();
    if (cambiaPass) { payload.password_actual = pActual; payload.password_nueva = pNueva; }
    if (Object.keys(payload).length === 0) return setErr("No hay cambios para guardar.");

    setBusy(true);
    try {
      const updated = await updateMe(payload);
      setMe(updated);
      setNombre(updated.nombre || "");
      setPActual(""); setPNueva(""); setPRepite("");
      setOk("Perfil actualizado.");
      setTimeout(() => setOk(""), 2500);
    } catch (e) {
      setErr(e.response?.data?.detail || "No se pudo guardar.");
    } finally { setBusy(false); }
  }

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      {/* Header */}
      <div className="card liquid p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-iris-500/20 text-iris-300 grid place-items-center text-[26px] font-display font-semibold shrink-0 ring-1 ring-iris-500/30">
          {inicial}
        </div>
        <div className="min-w-0">
          <h1 className="font-display text-[24px] font-semibold text-txt truncate">{me?.nombre || me?.email}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="pill text-iris-400 bg-iris-500/12 flex items-center gap-1">
              <Shield size={11} /> {ROL_LABEL[rol] || rol}
            </span>
            <span className="text-[13px] text-txt-mute truncate">{me?.email}</span>
          </div>
        </div>
      </div>

      {/* Datos del perfil */}
      <form onSubmit={guardar} className="card p-6 flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <User size={16} className="text-accent" />
          <span className="label text-accent">Datos del perfil</span>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="label">Nombre</label>
          <input className="input" value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Tu nombre" />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="label flex items-center gap-1.5"><Mail size={12} /> Email</label>
          <input className="input opacity-60 cursor-not-allowed" value={me?.email || ""} disabled />
          <span className="text-[11.5px] text-txt-mute">El email no se puede cambiar. Pedíselo a tu admin si hace falta.</span>
        </div>

        {/* Cambio de contraseña */}
        <div className="pt-2 border-t border-white/[0.06] flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <Lock size={14} className="text-txt-soft" />
            <span className="label">Cambiar contraseña</span>
            <span className="text-[11.5px] text-txt-mute">(opcional)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input className="input" type="password" placeholder="Actual" value={pActual}
                   onChange={(e) => setPActual(e.target.value)} autoComplete="current-password" />
            <input className="input" type="password" placeholder="Nueva" value={pNueva}
                   onChange={(e) => setPNueva(e.target.value)} autoComplete="new-password" />
            <input className="input" type="password" placeholder="Repetir nueva" value={pRepite}
                   onChange={(e) => setPRepite(e.target.value)} autoComplete="new-password" />
          </div>
        </div>

        {err && <div className="text-[13px] text-neg">{err}</div>}
        {ok && <div className="text-[13px] text-pos flex items-center gap-1.5"><Check size={14} /> {ok}</div>}

        <button type="submit" disabled={busy} className="btn-primary self-start flex items-center gap-2">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} Guardar cambios
        </button>
      </form>

      {/* Conexiones */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Plug size={16} className="text-accent" />
          <span className="label text-accent">Conexiones</span>
        </div>
        <Conexiones />
      </div>
    </div>
  );
}

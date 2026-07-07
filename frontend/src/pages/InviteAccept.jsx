import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2, Check } from "lucide-react";
import SalemetriqLogo from "../components/SalemetriqLogo";
import api from "../utils/api";
import { acceptInvite } from "../utils/auth";

export default function InviteAccept() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [info, setInfo] = useState(null);
  const [estado, setEstado] = useState("cargando"); // cargando | ok | invalida
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get(`/auth/invite/${token}`)
      .then((r) => { setInfo(r.data); setEstado("ok"); })
      .catch(() => setEstado("invalida"));
  }, [token]);

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (password.length < 6) return setError("La contraseña debe tener al menos 6 caracteres.");
    if (password !== password2) return setError("Las contraseñas no coinciden.");
    setSaving(true);
    try {
      const user = await acceptInvite(token, password);
      navigate(user?.is_superadmin ? "/clientes" : "/overview", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo activar la cuenta.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-4 mb-8">
          <SalemetriqLogo size={48} />
          <div className="text-center">
            <div className="font-brand text-xl text-txt">SALEMETRIQ</div>
            <div className="text-[11px] text-txt-mute uppercase tracking-[0.22em] mt-1">Activá tu cuenta</div>
          </div>
        </div>

        {estado === "cargando" && (
          <div className="card p-6 text-center text-[13.5px] text-txt-mute flex items-center justify-center gap-2">
            <Loader2 size={16} className="animate-spin" /> Validando invitación…
          </div>
        )}

        {estado === "invalida" && (
          <div className="card p-6 text-center flex flex-col gap-3">
            <div className="text-[14px] text-neg font-medium">Invitación inválida o vencida</div>
            <p className="text-[13px] text-txt-mute">Pedile a tu administrador que te genere una nueva.</p>
            <button onClick={() => navigate("/login")} className="btn-ghost text-[13px]">Ir al login</button>
          </div>
        )}

        {estado === "ok" && (
          <form onSubmit={submit} className="card p-6 flex flex-col gap-4">
            <div className="text-[13.5px] text-txt-soft">
              Hola <span className="text-txt font-medium">{info.nombre || info.email}</span>, te unís a{" "}
              <span className="text-txt font-medium">{info.workspace}</span> como{" "}
              <span className="text-accent">{info.rol}</span>. Definí tu contraseña:
            </div>
            <div>
              <label className="label">Contraseña</label>
              <input type="password" className="input mt-1.5" value={password}
                     onChange={(e) => setPassword(e.target.value)} autoFocus required />
            </div>
            <div>
              <label className="label">Repetir contraseña</label>
              <input type="password" className="input mt-1.5" value={password2}
                     onChange={(e) => setPassword2(e.target.value)} required />
            </div>
            {error && <div className="text-[13.5px] text-neg">{error}</div>}
            <button type="submit" className="btn-primary flex items-center justify-center gap-2" disabled={saving}>
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
              {saving ? "Activando…" : "Activar cuenta"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import SalemetriqLogo from "../components/SalemetriqLogo";
import { login } from "../utils/auth";

// Credenciales del usuario demo (workspace demo, aislado de los datos reales).
const DEMO = { email: "demo@salemetriq.com", password: "Demo2026!" };

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function ingresar(mail, pass) {
    setError("");
    setLoading(true);
    try {
      const user = await login(mail, pass);
      navigate(user?.is_superadmin ? "/clientes" : "/overview", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    ingresar(email, password);
  }

  function entrarDemo() {
    // Autocompleta los campos (para que se vean) y entra directo.
    setEmail(DEMO.email);
    setPassword(DEMO.password);
    ingresar(DEMO.email, DEMO.password);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center gap-4 mb-8">
          <SalemetriqLogo size={48} />
          <div className="text-center">
            <div className="font-brand text-xl text-txt">SALEMETRIQ</div>
            <div className="text-[11px] text-txt-mute uppercase tracking-[0.22em] mt-1">Sales Telemetry</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="card p-6 flex flex-col gap-4">
          <div>
            <label className="label">Email</label>
            <input
              type="email" className="input mt-1.5" value={email}
              onChange={(e) => setEmail(e.target.value)} autoFocus required
            />
          </div>
          <div>
            <label className="label">Contraseña</label>
            <input
              type="password" className="input mt-1.5" value={password}
              onChange={(e) => setPassword(e.target.value)} required
            />
          </div>
          {error && <div className="text-[13.5px] text-neg">{error}</div>}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Entrando…" : "Entrar"}
          </button>

          {/* Acceso demo — autocompleta y entra con el usuario demo */}
          <div className="flex items-center gap-3 my-1">
            <span className="h-px flex-1 bg-ink-line" />
            <span className="text-[11px] text-txt-mute uppercase tracking-[0.14em]">o</span>
            <span className="h-px flex-1 bg-ink-line" />
          </div>
          <button
            type="button" onClick={entrarDemo} disabled={loading}
            className="btn-ghost flex items-center justify-center gap-2 text-[13.5px]"
          >
            <Sparkles size={15} className="text-accent" /> Entrar como usuario demo
          </button>
          <p className="text-[11.5px] text-txt-mute text-center -mt-1">
            Explorá la plataforma con datos de ejemplo, sin registrarte.
          </p>
        </form>
      </div>
    </div>
  );
}

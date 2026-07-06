/**
 * Cliente de auth: login contra el backend, guarda JWT en localStorage,
 * helpers para obtener usuario actual y rol.
 */
import api from "./api";

const TOKEN_KEY = "smq_token";
const USER_KEY = "smq_user";

export async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  localStorage.setItem(TOKEN_KEY, data.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  return data.user;
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export function hasRole(...roles) {
  const u = getUser();
  return u && roles.includes(u.rol);
}

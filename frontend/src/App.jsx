import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import GlassFilters from "./components/GlassFilters";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Calls from "./pages/Calls";
import Closers from "./pages/Closers";
import Setters from "./pages/Setters";
import UserProfile from "./pages/UserProfile";
import CallAnalysis from "./pages/CallAnalysis";
import ScriptGenerator from "./pages/ScriptGenerator";
import { isAuthenticated } from "./utils/auth";

function RequireAuth({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <GlassFilters />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="calls" element={<Calls />} />
          <Route path="closers" element={<Closers />} />
          <Route path="setters" element={<Setters />} />
          <Route path="users/:id" element={<UserProfile />} />
          <Route path="call-analysis" element={<CallAnalysis />} />
          <Route path="script-generator" element={<ScriptGenerator />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

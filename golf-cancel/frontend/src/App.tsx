import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Watches from "./pages/Watches";
import Settings from "./pages/Settings";
import Notifications from "./pages/Notifications";

export default function App() {
  return (
    <div className="app">
      <nav className="nav">
        <h1>⛳ 골프 취소티</h1>
        <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "active" : "")}>대시보드</NavLink>
        <NavLink to="/watches" className={({ isActive }) => (isActive ? "active" : "")}>알림 조건</NavLink>
        <NavLink to="/notifications" className={({ isActive }) => (isActive ? "active" : "")}>알림 이력</NavLink>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>설정</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/watches" element={<Watches />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </div>
  );
}

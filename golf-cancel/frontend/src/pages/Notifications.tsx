import { useEffect, useState } from "react";
import { api, NotificationItem } from "../lib/api";

export default function Notifications() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [err, setErr] = useState("");

  const load = async () => {
    try { setItems(await api.listNotifications()); }
    catch (e: any) { setErr(e.message); }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>알림 이력</h2>
        <p className="muted" style={{ marginTop: 0 }}>최근 100건. 30초마다 자동 갱신됩니다.</p>
        {err && <div style={{ color: "var(--danger)" }}>{err}</div>}
        {items.length === 0 && <div className="muted">아직 발송된 알림이 없습니다.</div>}

        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "var(--muted)", borderBottom: "1px solid var(--border)" }}>
              <th style={{ padding: 8 }}>시각</th>
              <th>채널</th>
              <th>watch</th>
              <th>tee_time</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {items.map((n) => (
              <tr key={n.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: 8 }}>{new Date(n.sent_at).toLocaleString()}</td>
                <td>{n.channel}</td>
                <td>#{n.watch_id}</td>
                <td>#{n.tee_time_id}</td>
                <td style={{ color: n.success ? "var(--accent)" : "var(--danger)" }}>
                  {n.success ? "성공" : `실패 · ${n.error_msg ?? ""}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

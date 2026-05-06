import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, Course, KakaoStatus, REGIONS } from "../lib/api";

export default function Settings() {
  const [params] = useSearchParams();
  const [status, setStatus] = useState<KakaoStatus | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const flash = params.get("kakao");
  const flashMsg = params.get("msg");

  const load = async () => {
    setStatus(await api.kakaoStatus());
    setCourses(await api.listCourses());
  };
  useEffect(() => { load(); }, []);

  const test = async () => {
    setErr(""); setMsg("");
    try {
      await api.kakaoTest();
      setMsg("테스트 메시지를 보냈습니다. 카카오톡 '나에게 보내기' 채널을 확인하세요.");
    } catch (e: any) { setErr(e.message); }
  };

  const disconnect = async () => {
    if (!confirm("카카오 연결을 해제할까요?")) return;
    await api.kakaoDisconnect();
    await load();
  };

  const toggle = async (id: number) => {
    await api.toggleCourse(id);
    await load();
  };

  return (
    <div>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>카카오톡 알림 연결</h2>
        {flash === "ok" && <div className="badge green" style={{ marginBottom: 8 }}>연결되었습니다.</div>}
        {flash === "error" && <div style={{ color: "var(--danger)", marginBottom: 8 }}>실패: {flashMsg}</div>}

        {status?.connected ? (
          <>
            <div className="muted" style={{ marginBottom: 12 }}>
              연결됨 · 토큰 만료: {status.expires_at ? new Date(status.expires_at).toLocaleString() : "-"}
              <br />(만료 1분 전 자동 갱신됩니다)
            </div>
            <div className="row">
              <button className="primary" onClick={test}>테스트 메시지 보내기</button>
              <button onClick={disconnect}>연결 해제</button>
            </div>
          </>
        ) : (
          <>
            <p className="muted">카카오 디벨로퍼스에서 등록한 본인 계정으로 로그인 후, 백엔드가 본인 카카오톡으로 알림을 발송합니다.</p>
            <a className="btn primary" href="/api/kakao/login">카카오로 로그인</a>
          </>
        )}

        {msg && <div className="badge green" style={{ marginTop: 12 }}>{msg}</div>}
        {err && <div style={{ color: "var(--danger)", marginTop: 12 }}>{err}</div>}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>골프장 활성화</h2>
        <p className="muted" style={{ marginTop: 0 }}>비활성 처리하면 폴링 대상에서 제외됩니다.</p>

        {REGIONS.map((r) => {
          const items = courses.filter((c) => c.region === r.value);
          if (items.length === 0) return null;
          return (
            <div key={r.value} style={{ marginTop: 14 }}>
              <h4 style={{ margin: "8px 0" }}>{r.label} <span className="muted">({items.length})</span></h4>
              <div className="grid">
                {items.map((c) => (
                  <div key={c.id} className="row" style={{ justifyContent: "space-between",
                    background: "var(--panel-2)", padding: "8px 12px", borderRadius: 8,
                    border: "1px solid var(--border)" }}>
                    <div>
                      <div>{c.name}</div>
                      <div className="muted" style={{ fontSize: 12 }}>{c.platform}</div>
                    </div>
                    <button onClick={() => toggle(c.id)} className={c.is_active ? "primary" : ""}>
                      {c.is_active ? "활성" : "비활성"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

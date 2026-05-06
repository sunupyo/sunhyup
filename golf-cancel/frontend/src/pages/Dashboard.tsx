import { useEffect, useMemo, useState } from "react";
import { api, REGIONS, regionLabel, TeeTime, WEEKDAYS } from "../lib/api";

export default function Dashboard() {
  const [tts, setTts] = useState<TeeTime[]>([]);
  const [region, setRegion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      setTts(await api.listTeeTimes({ region: region || undefined }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [region]);

  const grouped = useMemo(() => {
    const by: Record<string, TeeTime[]> = {};
    for (const tt of tts) {
      const k = tt.region;
      if (!by[k]) by[k] = [];
      by[k].push(tt);
    }
    return by;
  }, [tts]);

  const onPollNow = async () => {
    setPolling(true);
    try {
      await api.pollNow();
      await load();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setPolling(false);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row">
            <label style={{ marginBottom: 0 }}>권역</label>
            <select value={region} onChange={(e) => setRegion(e.target.value)}>
              <option value="">전체</option>
              {REGIONS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
            <span className="muted">현재 열려있는 티타임: {tts.length}건</span>
          </div>
          <div className="row">
            <button onClick={load} disabled={loading}>새로고침</button>
            <button className="primary" onClick={onPollNow} disabled={polling}>
              {polling ? "크롤링 중..." : "지금 폴링"}
            </button>
          </div>
        </div>
        {err && <div style={{ color: "var(--danger)", marginTop: 8 }}>{err}</div>}
      </div>

      {Object.keys(grouped).length === 0 && !loading && (
        <div className="card muted">아직 잡힌 취소티가 없습니다. 우상단 "지금 폴링"으로 강제 실행해 보세요.</div>
      )}

      {REGIONS.map((r) => {
        const items = grouped[r.value];
        if (!items || items.length === 0) return null;
        return (
          <section key={r.value} style={{ marginBottom: 16 }}>
            <h3 style={{ margin: "16px 0 8px" }}>{r.label} <span className="muted">({items.length})</span></h3>
            <div className="grid">
              {items.map((tt) => <TeeCard key={tt.id} tt={tt} />)}
            </div>
          </section>
        );
      })}
    </div>
  );
}

function TeeCard({ tt }: { tt: TeeTime }) {
  const d = new Date(tt.play_date + "T00:00:00");
  const w = WEEKDAYS[(d.getDay() + 6) % 7];
  const isWeekend = d.getDay() === 0 || d.getDay() === 6;
  return (
    <a className="tee-card" href={tt.raw_url ?? "#"} target="_blank" rel="noreferrer">
      <div className="top">
        <div className="name">{tt.course_name}</div>
        <span className="badge">{regionLabel(tt.region)}</span>
      </div>
      <div className="time">{tt.tee_time.slice(0, 5)}</div>
      <div className="meta">
        {tt.play_date} ({w}) · {tt.holes}홀
        {isWeekend && <span className="badge" style={{ marginLeft: 6 }}>주말</span>}
      </div>
      <div className="meta">
        잔여 <b style={{ color: "var(--text)" }}>{tt.slots_open}</b>자리
        {tt.green_fee && <span className="fee" style={{ marginLeft: 8 }}>{tt.green_fee.toLocaleString()}원</span>}
      </div>
    </a>
  );
}

import { useEffect, useState } from "react";
import { api, Course, REGIONS, Region, Watch, WEEKDAYS } from "../lib/api";

type Form = Omit<Watch, "id" | "created_at">;

const empty: Form = {
  name: "",
  regions: [],
  course_ids: [],
  weekdays: [],
  time_min: null,
  time_max: null,
  date_from: null,
  date_to: null,
  max_green_fee: null,
  min_slots: 1,
  is_active: true,
};

export default function Watches() {
  const [list, setList] = useState<Watch[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [editing, setEditing] = useState<Form | null>(null);
  const [editId, setEditId] = useState<number | null>(null);
  const [err, setErr] = useState("");

  const load = async () => {
    try {
      const [w, c] = await Promise.all([api.listWatches(), api.listCourses()]);
      setList(w);
      setCourses(c);
    } catch (e: any) {
      setErr(e.message);
    }
  };
  useEffect(() => { load(); }, []);

  const startNew = () => { setEditing({ ...empty }); setEditId(null); };
  const startEdit = (w: Watch) => {
    const { id, created_at, ...rest } = w;
    setEditing(rest);
    setEditId(id);
  };

  const save = async () => {
    if (!editing) return;
    try {
      if (editId) await api.updateWatch(editId, editing);
      else await api.createWatch(editing);
      setEditing(null);
      setEditId(null);
      await load();
    } catch (e: any) { setErr(e.message); }
  };

  const remove = async (id: number) => {
    if (!confirm("삭제할까요?")) return;
    await api.deleteWatch(id);
    await load();
  };

  return (
    <div>
      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h2 style={{ margin: 0 }}>알림 조건</h2>
          <button className="primary" onClick={startNew}>+ 새 조건</button>
        </div>
        <p className="muted" style={{ marginTop: 8 }}>
          조건이 일치하는 새 취소티가 등장하면 카카오톡 "나에게" 알림을 보냅니다.
          여러 조건을 만들어두면 OR 로 매칭됩니다.
        </p>
      </div>

      {err && <div className="card" style={{ color: "var(--danger)" }}>{err}</div>}

      {editing && (
        <WatchForm
          form={editing}
          courses={courses}
          onChange={setEditing}
          onSave={save}
          onCancel={() => { setEditing(null); setEditId(null); }}
          editing={editId !== null}
        />
      )}

      <div className="grid">
        {list.map((w) => (
          <div key={w.id} className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <b>{w.name}</b>
              <span className={"badge" + (w.is_active ? " green" : "")}>
                {w.is_active ? "활성" : "비활성"}
              </span>
            </div>
            <div className="muted" style={{ fontSize: 13, marginTop: 6, lineHeight: 1.6 }}>
              {w.regions.length === 0 ? "전체 권역" : w.regions.map((r) =>
                REGIONS.find((x) => x.value === r)?.label ?? r
              ).join(", ")}
              <br />
              요일: {w.weekdays.length === 0 ? "전체" : w.weekdays.map((d) => WEEKDAYS[d]).join(",")}
              {(w.time_min || w.time_max) && <> · {w.time_min ?? ""}~{w.time_max ?? ""}</>}
              <br />
              {w.max_green_fee && <>그린피 ≤ {w.max_green_fee.toLocaleString()}원 · </>}
              잔여 ≥ {w.min_slots}
            </div>
            <div className="row" style={{ marginTop: 10 }}>
              <button onClick={() => startEdit(w)}>수정</button>
              <button onClick={() => remove(w.id)} style={{ color: "var(--danger)" }}>삭제</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function WatchForm({
  form, courses, onChange, onSave, onCancel, editing,
}: {
  form: Form;
  courses: Course[];
  onChange: (f: Form) => void;
  onSave: () => void;
  onCancel: () => void;
  editing: boolean;
}) {
  const set = (p: Partial<Form>) => onChange({ ...form, ...p });
  const toggleArr = <T,>(arr: T[], v: T) =>
    arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>{editing ? "조건 수정" : "새 알림 조건"}</h3>

      <div className="field">
        <label>이름</label>
        <input value={form.name} onChange={(e) => set({ name: e.target.value })} placeholder="예: 주말 새벽 골프" />
      </div>

      <div className="field">
        <label>권역 (다중 선택, 미선택 = 전체)</label>
        <div className="row">
          {REGIONS.map((r) => (
            <label key={r.value} style={{ display: "flex", gap: 4, alignItems: "center", marginBottom: 0 }}>
              <input
                type="checkbox"
                checked={form.regions.includes(r.value)}
                onChange={() => set({ regions: toggleArr(form.regions, r.value) as Region[] })}
              />
              {r.label}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <label>요일 (미선택 = 전체)</label>
        <div className="row">
          {WEEKDAYS.map((d, i) => (
            <label key={i} style={{ display: "flex", gap: 4, alignItems: "center", marginBottom: 0 }}>
              <input
                type="checkbox"
                checked={form.weekdays.includes(i)}
                onChange={() => set({ weekdays: toggleArr(form.weekdays, i) })}
              />
              {d}
            </label>
          ))}
        </div>
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label>시작 시각</label>
          <input type="time" value={form.time_min ?? ""} onChange={(e) => set({ time_min: e.target.value || null })} />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label>종료 시각</label>
          <input type="time" value={form.time_max ?? ""} onChange={(e) => set({ time_max: e.target.value || null })} />
        </div>
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label>날짜 시작</label>
          <input type="date" value={form.date_from ?? ""} onChange={(e) => set({ date_from: e.target.value || null })} />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label>날짜 종료</label>
          <input type="date" value={form.date_to ?? ""} onChange={(e) => set({ date_to: e.target.value || null })} />
        </div>
      </div>

      <div className="row">
        <div className="field" style={{ flex: 1 }}>
          <label>최대 그린피 (원)</label>
          <input
            type="number"
            value={form.max_green_fee ?? ""}
            onChange={(e) => set({ max_green_fee: e.target.value ? Number(e.target.value) : null })}
            placeholder="예: 250000"
          />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label>최소 잔여 자리</label>
          <input
            type="number"
            min={1}
            max={4}
            value={form.min_slots}
            onChange={(e) => set({ min_slots: Math.max(1, Number(e.target.value)) })}
          />
        </div>
      </div>

      <div className="field">
        <label>특정 골프장만 (미선택 = 전체)</label>
        <select
          multiple
          size={Math.min(8, Math.max(3, courses.length))}
          value={form.course_ids.map(String)}
          onChange={(e) => {
            const ids = Array.from(e.target.selectedOptions).map((o) => Number(o.value));
            set({ course_ids: ids });
          }}
          style={{ width: "100%" }}
        >
          {courses.map((c) => (
            <option key={c.id} value={c.id}>
              [{REGIONS.find((r) => r.value === c.region)?.label ?? c.region}] {c.name}
            </option>
          ))}
        </select>
      </div>

      <div className="field">
        <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => set({ is_active: e.target.checked })}
          />
          활성화
        </label>
      </div>

      <div className="row">
        <button className="primary" onClick={onSave} disabled={!form.name}>저장</button>
        <button onClick={onCancel}>취소</button>
      </div>
    </div>
  );
}

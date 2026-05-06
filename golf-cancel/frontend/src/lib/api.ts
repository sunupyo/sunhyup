export type Region = "GG_SOUTH" | "GG_NORTH" | "GG_EAST_GW" | "CHUNGCHEONG";

export const REGIONS: { value: Region; label: string }[] = [
  { value: "GG_SOUTH", label: "경기 남부" },
  { value: "GG_NORTH", label: "경기 북부" },
  { value: "GG_EAST_GW", label: "경기 동부 + 강원" },
  { value: "CHUNGCHEONG", label: "충청권" },
];

export const WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"];

export interface Course {
  id: number;
  name: string;
  region: Region;
  platform: string;
  booking_url: string | null;
  is_active: boolean;
}

export interface TeeTime {
  id: number;
  course_id: number;
  course_name: string;
  region: Region;
  play_date: string;
  tee_time: string;
  holes: number;
  green_fee: number | null;
  slots_open: number;
  raw_url: string | null;
  status: string;
  first_seen_at: string;
}

export interface Watch {
  id: number;
  name: string;
  regions: Region[];
  course_ids: number[];
  weekdays: number[];
  time_min: string | null;
  time_max: string | null;
  date_from: string | null;
  date_to: string | null;
  max_green_fee: number | null;
  min_slots: number;
  is_active: boolean;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  watch_id: number;
  tee_time_id: number;
  sent_at: string;
  channel: string;
  success: boolean;
  error_msg: string | null;
}

export interface KakaoStatus {
  connected: boolean;
  expires_at: string | null;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`${r.status} ${txt}`);
  }
  if (r.status === 204) return undefined as unknown as T;
  return r.json();
}

export const api = {
  // courses
  listCourses: (region?: string) =>
    http<Course[]>(`/api/courses${region ? `?region=${region}` : ""}`),
  toggleCourse: (id: number) =>
    http<Course>(`/api/courses/${id}/toggle`, { method: "PATCH" }),

  // teetimes
  listTeeTimes: (params: { region?: string; course_id?: number; date_from?: string; date_to?: string } = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v != null && qs.append(k, String(v)));
    return http<TeeTime[]>(`/api/teetimes?${qs.toString()}`);
  },

  // watches
  listWatches: () => http<Watch[]>("/api/watches"),
  createWatch: (w: Omit<Watch, "id" | "created_at">) =>
    http<Watch>("/api/watches", { method: "POST", body: JSON.stringify(w) }),
  updateWatch: (id: number, w: Omit<Watch, "id" | "created_at">) =>
    http<Watch>(`/api/watches/${id}`, { method: "PUT", body: JSON.stringify(w) }),
  deleteWatch: (id: number) =>
    http<{ ok: boolean }>(`/api/watches/${id}`, { method: "DELETE" }),

  // notifications
  listNotifications: () => http<NotificationItem[]>("/api/notifications"),

  // kakao
  kakaoStatus: () => http<KakaoStatus>("/api/kakao/status"),
  kakaoTest: () => http<{ ok: boolean }>("/api/kakao/test", { method: "POST" }),
  kakaoDisconnect: () => http<{ ok: boolean }>("/api/kakao/disconnect", { method: "DELETE" }),

  // admin
  pollNow: () => http<{ ok: boolean }>("/api/admin/poll-now", { method: "POST" }),
};

export function regionLabel(r: string) {
  return REGIONS.find((x) => x.value === r)?.label ?? r;
}

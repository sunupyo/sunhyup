# 골프 취소티 알리미 (Golf Cancel Notifier)

더블이글(dbegl.com)을 벤치마킹한 **개인용** 골프 취소티 알림 플랫폼.
- 백엔드: Python (FastAPI + SQLAlchemy + APScheduler)
- 프론트엔드: React + Vite + TypeScript
- 알림: 카카오톡 "나에게 보내기" (사업자/심사 불필요)
- 폴링: 1분 간격
- 권역: 경기 남부 / 경기 북부 / 경기 동부+강원 / 충청권

> **중요**: 첫 실행에서는 데모 모드(`ENABLE_DEMO_CRAWLER=true`)로 가상의 취소티가 생성됩니다.
> 실제 골프장 크롤링은 `backend/app/crawlers/xgolf.py`의 엔드포인트/페이로드를 검증한 뒤 활성화합니다.

---

## 1. 사전 준비 — 카카오 디벨로퍼스 앱 등록

1. https://developers.kakao.com 접속 → 본인 카카오 계정으로 로그인
2. **내 애플리케이션 → 애플리케이션 추가하기**
   - 앱 이름: `골프 취소티 알리미` (자유)
   - 사업자명: 본인 이름
3. 생성된 앱 진입 → **앱 키** 메뉴
   - **REST API 키** 복사 → `.env` 의 `KAKAO_REST_API_KEY`
4. **플랫폼 → Web 플랫폼 등록**
   - 사이트 도메인: `http://localhost:8000`
5. **카카오 로그인 → 활성화 ON**
6. **카카오 로그인 → Redirect URI 등록**
   - `http://localhost:8000/api/kakao/callback`
7. **카카오 로그인 → 동의항목**
   - **카카오톡 메시지 전송** (`talk_message`) → "필수 동의"로 설정

---

## 2. 백엔드 실행

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 를 열어 KAKAO_REST_API_KEY 채우기

python run.py
```

- 서버: http://localhost:8000
- 헬스체크: http://localhost:8000/api/health
- API 문서(자동 생성): http://localhost:8000/docs

처음 실행 시 자동으로:
- SQLite DB(`golf.db`) 생성
- 4개 권역 골프장 시드 데이터 삽입 (40여 곳)
- 1분 간격 크롤링 스케줄러 시작 (데모 모드)

---

## 3. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저: http://localhost:5173

---

## 4. 카카오 연결 + 첫 알림 받기

1. 프론트 `설정` 탭 → **카카오로 로그인** 클릭
2. 카카오 인증 → 자동으로 `/settings?kakao=ok` 로 복귀
3. **테스트 메시지 보내기** 클릭 → 카카오톡 "나에게 보내기" 채널 확인
4. `알림 조건` 탭 → **+ 새 조건** 으로 알림 조건 등록
   - 예: "주말 새벽" → 권역 모두, 요일 토/일, 시간 06:00~09:00, 최대 그린피 250,000원
5. 활성화 후 1~2분 안에 데모 데이터 기반으로 카카오 알림이 도착합니다.

---

## 5. 실 데이터 크롤러 활성화 절차 (Phase 2)

데모로 파이프라인이 잘 도는 것을 확인했으면:

1. **XGOLF 엔드포인트 확인**
   - 크롬에서 `xgolf.com` 로그인 → DevTools → Network → Fetch/XHR
   - 골프장 예약 페이지에서 잔여 티타임을 가져오는 요청을 찾기
   - URL, payload, 응답 JSON 키 확인
2. `backend/app/crawlers/xgolf.py` 의 `_ENDPOINT`, `_build_payload`, `_parse_response` 수정
3. `backend/.env` 에서 `ENABLE_DEMO_CRAWLER=false`
4. `backend/app/courses_seed.py` 또는 DB에서 각 골프장의 `platform_course_id`, `booking_url` 입력
   - SQLite GUI(예: TablePlus, DB Browser) 또는 `/api/courses` REST API 사용
5. 백엔드 재시작 → 1분 후부터 실제 잔여티 모니터링 시작

다른 플랫폼(KGOLF, 골프존카운티 등)을 추가하려면:
- `backend/app/crawlers/` 에 새 파일 추가, `BaseCrawler` 상속
- `crawlers/registry.py` 에 등록
- `models.py` 의 `Platform` enum에 항목 추가

---

## 6. 디렉터리 구조

```
golf-cancel/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 진입점, 스케줄러 부팅
│   │   ├── config.py           # 환경변수
│   │   ├── db.py               # SQLAlchemy
│   │   ├── models.py           # Course / TeeTime / Watch / Notification / KakaoToken
│   │   ├── schemas.py          # Pydantic
│   │   ├── kakao.py            # OAuth + 나에게 보내기
│   │   ├── notifier.py         # Watch 매칭 + 메시지 포맷
│   │   ├── scheduler.py        # 1분 폴링 + diff 로직
│   │   ├── courses_seed.py     # 4권역 골프장 시드
│   │   ├── crawlers/
│   │   │   ├── base.py
│   │   │   ├── demo.py         # 가상 데이터 (검증용)
│   │   │   ├── xgolf.py        # 실제 크롤러 (엔드포인트 검증 필요)
│   │   │   └── registry.py
│   │   └── api/
│   │       ├── courses.py
│   │       ├── teetimes.py
│   │       ├── watches.py
│   │       ├── notifications.py
│   │       ├── kakao_oauth.py
│   │       └── admin.py
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── main.tsx
    │   ├── index.css
    │   ├── lib/api.ts
    │   └── pages/
    │       ├── Dashboard.tsx
    │       ├── Watches.tsx
    │       ├── Notifications.tsx
    │       └── Settings.tsx
    ├── index.html
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

## 7. 주요 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 상태체크 |
| GET | `/api/courses?region=GG_SOUTH` | 골프장 목록 |
| PATCH | `/api/courses/{id}/toggle` | 활성/비활성 |
| GET | `/api/teetimes?region=...` | 현재 열린 취소티 |
| GET/POST/PUT/DELETE | `/api/watches[/{id}]` | 알림 조건 CRUD |
| GET | `/api/notifications` | 알림 발송 이력 |
| GET | `/api/kakao/login` | 카카오 OAuth 시작 (브라우저로 열기) |
| GET | `/api/kakao/callback` | OAuth 콜백 |
| GET | `/api/kakao/status` | 연결 상태 |
| POST | `/api/kakao/test` | 테스트 메시지 |
| DELETE | `/api/kakao/disconnect` | 연결 해제 |
| POST | `/api/admin/poll-now` | 수동 폴링 1회 |

---

## 8. FAQ

**Q. dbegl.com 처럼 알림톡(템플릿)을 못 쓰나요?**
알림톡은 사업자등록 + 카카오 비즈니스 채널 + 템플릿 심사가 필요합니다. 본인용에는 "나에게 보내기"가 무료/심사없음/즉시사용 가능해서 정확히 적합합니다.

**Q. 폴링 주기를 더 짧게 해도 되나요?**
법적/기술적으로 가능은 하지만 골프장 사이트의 부하/차단 정책을 고려해 1분 권장. 10초로 떨어뜨리면 IP 차단당하기 쉽습니다.

**Q. 클라우드 배포는?**
- 로컬 노트북 24시간 켜두기 (가장 간단)
- Render / Fly.io / Railway 무료 티어
- 라즈베리파이 + crontab 으로 항상 켜기

배포 시 `KAKAO_REDIRECT_URI` 와 카카오 디벨로퍼스의 Redirect URI 등록을 운영 도메인으로 변경.

**Q. 토큰이 만료되나요?**
- access_token: 6시간 (만료 1분 전 자동 갱신)
- refresh_token: 2개월 (이 기간 안에 한 번이라도 발송하면 자동 연장)
- 2개월간 한 번도 사용하지 않으면 재로그인 필요

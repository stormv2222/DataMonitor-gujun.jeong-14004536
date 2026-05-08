# DataMonitor POC 계획

## 1. 목표

현재 저장된 데이터 상태를 콘솔에서 실시간으로 조회할 수 있는 관리자 도구를 POC 형태로 구현한다.  
파일 읽기 레이어는 [DataPersistence](https://github.com/stormv2222/DataPersistence-gujun.jeong-14004536) 레포지토리의 JSON I/O를 재사용하고, 전체 구조는 [ConsoleMVC](https://github.com/stormv2222/ConsoleMVC-gujun.jeong-14004536) 스켈레톤의 MVC 패턴을 따른다.  
데이터 조작(추가·수정·삭제)은 이 도구의 범위 밖이며, 읽기 전용으로 동작한다.

---

## 2. 참고 레포 분석

### DataPersistence

| 구성요소 | 역할 | 재사용 여부 |
|---|---|---|
| `json_lib/` | 커스텀 JSON 파서 (lexer → parser → serializer) | 그대로 복사 |
| `app/repository.py` | JSON 파일 기반 CRUD | 읽기 메서드만 Model 레이어에 흡수 |
| `app/console.py` | 메뉴 기반 CRUD 콘솔 앱 | Controller + View로 대체 (조회·검색만) |

**데이터 파일 구조 (`records.json`)**

```json
{
  "next_id": 3,
  "records": [
    { "id": 1, "name": "Alice", "age": "30" },
    { "id": 2, "name": "Bob",   "age": "25" }
  ]
}
```

### ConsoleMVC

MVC 의존성 방향: `main.py` → `Controller` → (`Model`, `View`)

| 레이어 | ConsoleMVC 파일 | 역할 |
|---|---|---|
| Model | `models/user.py` | `User` dataclass + `UserRepository` (인메모리) |
| View | `views/user_view.py` | 출력 전담 (`show_*`, `get_input`) |
| Controller | `controllers/user_controller.py` | CRUD 흐름 조율, `run()` 메뉴 루프 |
| Wiring | `main.py` | Repository → View → Controller 생성 후 `run()` 호출 |

---

## 3. MVC 역할 매핑

| MVC 레이어 | ConsoleMVC | DataMonitor |
|---|---|---|
| **Model** | `User` + `UserRepository` (인메모리 dict) | `Record` + `RecordRepository` (json_lib 파일 읽기 전용) |
| **View** | `UserView` | `MonitorView` (대시보드 자동 갱신 포함) |
| **Controller** | `UserController` | `MonitorController` (조회·검색 + 파일 감시 기반 자동 갱신) |
| **인프라** | — | `FileWatcher` (MVC 외부, Controller에 주입) |

---

## 4. 기술 스택

- **언어**: Python 3.11+
- **외부 의존성 없음**: Python 표준 라이브러리만 사용 (`os`, `time`, `threading`, `sys`, `dataclasses`)
- **JSON I/O**: `json_lib` (DataPersistence에서 복사)
- **파일 변경 감지**: `os.path.getmtime()` 폴링 방식 (watchdog 미사용)
- **콘솔 UI**: ANSI 이스케이프 코드 + 화면 지우기(cls/clear) 재출력 방식

---

## 5. 디렉토리 구조

```
DataMonitor/
├── docs/
│   └── plan.md
├── data/
│   └── records.json            # 모니터링 대상 데이터 파일 (자동 생성)
├── json_lib/                   # DataPersistence에서 복사
│   ├── __init__.py
│   ├── lexer.py
│   ├── parser.py
│   └── serializer.py
├── models/                     # Model 레이어
│   ├── __init__.py
│   └── record.py               # Record (dataclass) + RecordRepository
├── views/                      # View 레이어
│   ├── __init__.py
│   └── monitor_view.py         # MonitorView (출력 전담)
├── controllers/                # Controller 레이어
│   ├── __init__.py
│   └── monitor_controller.py   # MonitorController (CRUD 흐름 + 자동 갱신)
├── app/                        # MVC 외부 인프라
│   ├── __init__.py
│   └── watcher.py              # FileWatcher (파일 변경 감지기)
└── main.py                     # Wiring: Repository → View → Watcher → Controller
```

---

## 6. 각 레이어 시그니처

### Model — `models/record.py`

ConsoleMVC의 `User` + `UserRepository` 패턴을 따르되, 저장소는 인메모리 dict 대신 `json_lib` 기반 파일로 교체한다.

```
Record (dataclass)
├── id: int          ← 파일에서 읽어온 값 그대로 사용
└── (동적 필드)      ← dict로 관리 (사용자 정의 key-value)

RecordRepository  ← 읽기 전용
├── __init__(file_path)
├── read_all()           → list[Record]
├── read_one(id)         → Record | None
└── search(key, value)   → list[Record]
```

### View — `views/monitor_view.py`

ConsoleMVC의 `UserView`와 동일한 원칙: 출력만 담당, 비즈니스 로직 없음.

```
MonitorView
├── show_dashboard(records, last_modified) ← 전체 대시보드 (자동 갱신 시 호출)
├── show_record(record)                    ← 단건 상세 출력
├── show_message(message)                  ← 안내/오류 메시지
└── get_input(prompt) → str               ← input() 래핑, strip() 적용
```

### Controller — `controllers/monitor_controller.py`

ConsoleMVC의 `UserController`와 동일한 구조. `run()`이 메뉴 루프 진입점이며, `FileWatcher`를 추가로 주입받아 자동 갱신을 담당한다.

```
MonitorController
├── __init__(repository, view, watcher)
├── list_records()
├── search_records()
└── run()   ← 메뉴 루프(s/q) + 파일 변경 시 view.show_dashboard() 재호출
```

### 인프라 — `app/watcher.py`

MVC 외부 컴포넌트. Controller에 의존성 주입 형태로 전달된다.

```
FileWatcher
├── __init__(file_path, callback, interval=1.0)
├── start() → 백그라운드 스레드 시작
└── stop()  → 스레드 종료
```

### Wiring — `main.py`

ConsoleMVC의 `main.py`와 동일한 책임: 레이어를 생성하고 주입한 뒤 `run()` 호출.

```python
repo       = RecordRepository('data/records.json')
view       = MonitorView()
watcher    = FileWatcher('data/records.json', callback=...)
controller = MonitorController(repo, view, watcher)
controller.run()
```

---

## 7. 구현 단계

### Phase 1 — 프로젝트 세팅

- 디렉토리 골격(`models/`, `views/`, `controllers/`, `app/`, `data/`, `json_lib/`) 생성
- `json_lib/`를 DataPersistence 레포에서 복사
- 초기 `data/records.json` 시드 데이터 작성 (레코드 3~5건)

**완료 기준**: `python -c "import json_lib"` 오류 없이 실행된다.

---

### Phase 2 — Model (`models/record.py`)

- `Record` dataclass 구현 (파일에서 읽어온 필드를 그대로 보존)
- `RecordRepository` 구현 (DataPersistence JSON I/O 기반, 읽기 메서드만 구현)

**완료 기준**: `RecordRepository`로 read_all/read_one/search 각각 정상 동작한다.

---

### Phase 3 — View (`views/monitor_view.py`)

- `show_dashboard`: cls/clear 후 헤더·레코드 목록·명령어 안내를 재출력
- `show_record`: 단건 상세 포맷 출력
- `show_message`: 단순 print 래핑
- `get_input`: `input()` + `strip()`

**완료 기준**: View 메서드를 직접 호출하면 의도한 포맷으로 출력된다.

---

### Phase 4 — 인프라 (`app/watcher.py`)

- `FileWatcher`: `os.path.getmtime()` 1초 폴링, 변경 감지 시 callback 호출
- `threading.Thread(daemon=True)`로 백그라운드 실행

**완료 기준**: records.json 수정 후 1~2초 내 callback이 호출된다.

---

### Phase 5 — Controller + 통합 (`controllers/monitor_controller.py`, `main.py`)

- `MonitorController.__init__`: `FileWatcher`의 callback을 `view.show_dashboard()` 재호출로 연결
- `run()`: 메뉴 루프 구현 (s: 검색, q: 종료)
- `main.py`: 레이어 Wiring

**완료 기준**: `python main.py` 실행 → 대시보드 출력 → 검색 동작 → 파일 변경 시 자동 갱신 전체 흐름이 동작한다.

---

## 8. 각 Phase별 검증 시나리오

| Phase | 검증 방법 |
|---|---|
| 1 | `import json_lib` import 성공 |
| 2 | `RecordRepository` read_all/read_one/search 각각 정상 동작 |
| 3 | View 메서드 직접 호출 시 의도한 포맷 출력 |
| 4 | records.json 수정 후 1~2초 내 callback 호출 확인 |
| 5 | 전체 흐름: 실행 → 대시보드 조회 → 검색 → 파일 변경 시 자동 갱신 확인 |

---

## 9. POC 범위 외 항목

POC이므로 아래 항목은 구현하지 않는다.

- 네트워크 기반 원격 모니터링
- 다중 파일 동시 감시
- 로그 이력/변경 이력 저장
- 인증·권한 처리
- 페이지네이션 (레코드 수가 적다고 가정)

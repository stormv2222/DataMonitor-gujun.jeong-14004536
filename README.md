# DataMonitor

JSON 파일에 저장된 데이터 상태를 콘솔에서 실시간으로 조회할 수 있는 관리자 도구 POC.

## 개요

- JSON 파일을 감시하며 변경 시 콘솔 화면을 자동 갱신 (읽기 전용)
- 콘솔 명령어로 레코드 검색
- 외부 라이브러리 없이 Python 표준 라이브러리만 사용
- MVC 패턴 적용 ([ConsoleMVC](https://github.com/stormv2222/ConsoleMVC-gujun.jeong-14004536) 스켈레톤 기반)
- 파일 읽기 레이어는 [DataPersistence](https://github.com/stormv2222/DataPersistence-gujun.jeong-14004536) 레포지토리의 JSON I/O 재사용

## 요구 사항

- Python 3.11 이상
- 외부 패키지 없음 (표준 라이브러리만 사용)

## 실행

```bash
python main.py
```

`data/records.json`이 없으면 자동으로 생성된다.

## 화면 예시

```
=== DataMonitor === [갱신: 2026-05-08 10:30:00]
총 레코드: 5건  |  필드: name, department, level

  [ID: 1]  name=Alice  department=Engineering  level=Senior
  [ID: 2]  name=Bob    department=Design       level=Mid
  [ID: 3]  name=Carol  department=Engineering  level=Junior
  [ID: 4]  name=Dave   department=Product      level=Senior
  [ID: 5]  name=Eve    department=Design       level=Senior

명령어: (s)검색  (q)종료
>
```

파일이 외부에서 변경되면 1초 이내에 화면이 자동 갱신된다.

## 명령어

| 키 | 동작 |
|---|---|
| `s` | 필드·값으로 검색 |
| `q` | 종료 |

## 데이터 파일 구조

`data/records.json`

```json
{
  "next_id": 6,
  "records": [
    { "id": 1, "name": "Alice", "department": "Engineering", "level": "Senior" }
  ]
}
```

- `next_id`: 다음 레코드 ID (읽기 전용)
- `records`: 레코드 배열. `id` 및 필드 구성은 파일에 저장된 값을 그대로 읽어 표시

## 아키텍처

MVC 의존성 방향: `main.py` → `Controller` → (`Model`, `View`)

```
models/record.py          — Record dataclass + RecordRepository (json_lib 기반 읽기 전용)
views/monitor_view.py     — MonitorView (출력 전담)
controllers/
  monitor_controller.py   — MonitorController (조회·검색 + 자동 갱신)
app/watcher.py            — FileWatcher (파일 변경 감지, MVC 외부 인프라)
json_lib/                 — 커스텀 JSON 파서 (lexer → parser → serializer)
```

## 테스트

```bash
# 전체 테스트 실행
python -m unittest discover -s tests -v

# 레이어별 단독 실행
python -m unittest tests.test_model      -v
python -m unittest tests.test_view       -v
python -m unittest tests.test_watcher    -v
python -m unittest tests.test_controller -v
```

총 52개 테스트 케이스.

## 프로젝트 구조

```
DataMonitor/
├── data/
│   └── records.json
├── json_lib/
├── models/
│   └── record.py
├── views/
│   └── monitor_view.py
├── controllers/
│   └── monitor_controller.py
├── app/
│   └── watcher.py
├── tests/
│   ├── test_model.py
│   ├── test_view.py
│   ├── test_watcher.py
│   └── test_controller.py
├── main.py
└── docs/
    └── plan.md
```

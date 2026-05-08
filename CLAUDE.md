# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

JSON 파일에 저장된 데이터 상태를 콘솔에서 실시간으로 조회할 수 있는 관리자 도구 POC.  
파일 읽기 레이어는 [DataPersistence](https://github.com/stormv2222/DataPersistence-gujun.jeong-14004536) 레포지토리의 JSON I/O를 재사용하고, 전체 구조는 [ConsoleMVC](https://github.com/stormv2222/ConsoleMVC-gujun.jeong-14004536) 스켈레톤의 MVC 패턴을 따른다.

## 실행

```bash
python main.py
```

`data/records.json`이 없으면 자동 생성된다.

## 아키텍처

MVC 의존성 방향: `main.py` → `Controller` → (`Model`, `View`)

```
main.py  (Wiring)
  ├── RecordRepository  →  models/record.py      [Model]
  ├── MonitorView       →  views/monitor_view.py [View]
  ├── FileWatcher       →  app/watcher.py        [인프라, Controller에 주입]
  └── MonitorController →  controllers/monitor_controller.py [Controller]
          │
          ├── _repo  (RecordRepository)   ← 읽기 전용 조회
          ├── _view  (MonitorView)        ← 화면 출력
          └── _watcher (FileWatcher)      ← 파일 변경 시 view.show_dashboard() 재호출
```

### 레이어별 책임

- **Model** (`models/record.py`): `Record` dataclass(id 포함) + `RecordRepository`(json_lib 기반 파일 읽기). DataPersistence의 JSON I/O 로직을 MVC Model로 재구성. 쓰기 기능 없음.
- **View** (`views/monitor_view.py`): 출력만 담당. `show_dashboard(records, last_modified)`로 전체 대시보드 재출력, `show_record`, `show_message`, `get_input`. 비즈니스 로직 없음.
- **Controller** (`controllers/monitor_controller.py`): `__init__`에서 `RecordRepository`, `MonitorView`, `FileWatcher`를 주입받음. `run()`이 메뉴 루프 진입점(s/q). 파일 변경 감지 시 `view.show_dashboard()` 재호출로 자동 갱신.
- **인프라** (`app/watcher.py`): `FileWatcher` — `os.path.getmtime()` 1초 폴링으로 파일 변경을 감지하고 callback을 호출하는 백그라운드 스레드. MVC 외부 컴포넌트로 Controller에 주입.
- **Wiring** (`main.py`): `RecordRepository` → `MonitorView` → `FileWatcher` → `MonitorController` 순으로 생성 후 `controller.run()` 호출.

## 설계 제약

- **외부 패키지 금지**: `os`, `time`, `threading`, `sys`, `dataclasses` 등 표준 라이브러리만 사용. `watchdog`, `rich`, `curses` 등 설치형 라이브러리 사용 불가.
- **JSON I/O는 반드시 `json_lib`**: `import json` 대신 `import json_lib`을 사용한다.
- **읽기 전용**: 데이터 파일에 대한 쓰기(추가·수정·삭제) 기능을 구현하지 않는다. `RecordRepository`는 읽기 메서드(`read_all`, `read_one`, `search`)만 제공한다.
- **데이터 파일 스키마**: `{"next_id": int, "records": [{id, ...fields}]}` 구조를 읽기만 한다.
- **View는 출력 전담**: View에 조건 분기나 데이터 가공 로직을 두지 않는다. 가공은 Controller에서 마친 후 View에 전달한다.
- **POC 범위**: 단일 파일 감시, 단일 사용자 콘솔만 지원. 원격 모니터링, 다중 파일, 변경 이력, 인증은 구현하지 않는다.

## 상세 구현 계획

`docs/plan.md` 참고. Phase 1~5로 구성되어 있으며 각 Phase마다 완료 기준이 명시되어 있다.

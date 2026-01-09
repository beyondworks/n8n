---
description: n8n 변환 노드 상세 가이드 (Code, Set, IF, Merge, Switch)
---

# n8n Transform Nodes Guide

변환(Transform) 노드는 데이터의 구조를 변경하거나 흐름을 제어하는 핵심 노드입니다.

## 💻 Code Node (`n8n-nodes-base.code`)

가장 강력한 노드로, JavaScript 또는 Python 코드를 실행합니다.

### 1. 언어 지원
- **JavaScript (기본)**: V8 엔진 기반. 모든 표준 JS 기능 사용 가능.
- **Python**: v1.0+ 부터 정식 지원.

### 2. 데이터 접근 및 반환
- **입력 데이터**: `$input.all()` (배열 형태) 또는 `$input.item` (단일 아이템)
- **JSON 데이터 접근**: `item.json.myField`
- **반환 형식**: 반드시 **객체 배열** 형태여야 합니다.
  ```javascript
  // Good
  return [{json: {result: "success"}}];
  
  // Good (Multiple items)
  return [
    {json: {id: 1, name: "A"}},
    {json: {id: 2, name: "B"}}
  ];
  ```

### 3. 유용한 내장 변수
- `$json`: 현재 아이템의 JSON 데이터
- `$node`: 다른 노드의 데이터 참조 (예: `$node["Webhook"].json.body`)
- `$vars`: 워크플로우 전역 변수 (환경변수와 다름, 실행 중 임시 저장)
- `$env`: 환경 변수 접근

---

## 📝 Set Node (`n8n-nodes-base.set`) (Edit Fields)

데이터 필드를 추가, 수정, 삭제합니다. 복잡한 코딩 없이 간단한 변수 설정에 사용합니다.

### 주요 기능
- **Values to Set**:
  - `String`: 고정 문자열
  - `Number`: 숫자
  - `Boolean`: 참/거짓
  - `Expression`: n8n 표현식 (예: `{{ $json.price * 1.1 }}`)
- **Keep Only Set**: 체크 시, 여기서 설정한 필드 외의 기존 필드는 모두 삭제됩니다. (데이터 클렌징에 유용)

---

## 🔀 조건 및 분기 (Logic)

### 1. IF Node (`n8n-nodes-base.if`)
조건에 따라 `True` 또는 `False` 경로로 분기합니다.
- **조건식**: 문자열 비교, 숫자 대소 비교, 정규식 매칭, 비어있음 확인 등 다양한 조건 제공.

### 2. Switch Node (`n8n-nodes-base.switch`)
하나의 값에 대해 여러 경로(3개 이상)로 분기할 때 사용합니다. (Java/C의 switch문과 동일)

---

## 🔗 Merge Node (`n8n-nodes-base.merge`)

두 개 이상의 데이터 흐름을 하나로 합칩니다.

### 주요 모드 (Mode)
1. **Append**: 단순히 데이터를 순서대로 이어 붙입니다. (Input 1 뒤에 Input 2 감음)
2. **Combine (Merge By Fields)**: SQL의 JOIN과 같습니다.
   - **Fields to Match**: 두 입력에서 일치해야 하는 키 필드 지정 (예: `email`, `id`)
   - **Output Type**:
     - `Keep Matches`: 교집합 (Inner Join)
     - `Keep Everything`: 합집합 (Full Outer Join)
     - `Enrich Input 1`: Input 1 기준 Left Join
3. **Merge By Position**: 순서대로 1:1 매칭합니다. (첫 번째끼리, 두 번째끼리...)

---

## 💡 레거시 노드 주의
- **Function Node**: `Code` 노드의 구 버전입니다. 새 워크플로우에서는 `Code` 노드를 사용하세요.
- **HTML Extract**: `HTML` 노드로 대체되었습니다.

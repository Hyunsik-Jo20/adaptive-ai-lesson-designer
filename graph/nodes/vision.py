from __future__ import annotations
from pathlib import Path
from services.openai_service import create_client, call_vision_json

def build_prompt(state: dict) -> str:
    lesson_input = state.get("lesson_input", {})
    teacher_intent = state.get("teacher_intent", {})
    return f"""
당신은 초등 교과서와 지도서를 분석하는 전문가임.
반드시 JSON만 출력할 것.
수업자 의도와 비전 분석 결과는 공동 기초값이 되어야 함.

과목: {lesson_input.get('subject','')}
학년: {lesson_input.get('grade','')}
학기: {lesson_input.get('semester','')}
단원: {lesson_input.get('unit','')}
차시 주제: {lesson_input.get('lesson_topic','')}
학습 목표: {lesson_input.get('learning_objectives','')}
수업자 의도: {teacher_intent.get('raw_text','')}
추가 지침: {state.get('prompt_settings',{}).get('vision','')}

분석 절차:
1. 이미지의 차시 제목과 문제 번호 구조를 파악
2. 번호가 보이는 문제 블록을 분리
3. 각 문제 블록별 지시문/문제유형/제시 자료/요구 사고를 정리
4. 핵심 개념과 기능을 추출
5. 문제들을 3개 내외의 활동 흐름으로 재구성
6. 이후 단계용 tool_hints, model_hints, lesson_plan_hints, worksheet_hints를 생성

출력 JSON 스키마:
{{
  "lesson_context": {{
    "lesson_title": "",
    "subject": "",
    "grade_hint": "",
    "page_scope": "",
    "total_problem_blocks": 0
  }},
  "core_concepts": [],
  "math_skills": [],
  "problem_blocks": [
    {{
      "problem_no": 1,
      "instruction": "",
      "task_type": "",
      "given_elements": [],
      "required_thinking": [],
      "concepts": [],
      "teacher_intent": "",
      "student_action": "",
      "materials": [],
      "possible_misconceptions": []
    }}
  ],
  "activity_flow": [
    {{
      "activity_name": "",
      "linked_problem_nos": [],
      "activity_purpose": "",
      "teacher_focus": "",
      "student_focus": ""
    }}
  ],
  "tool_hints": [],
  "model_hints": [],
  "lesson_plan_hints": [],
  "worksheet_hints": []
}}
"""

def node(state: dict) -> dict:
    api_key = state.get("api_key", "").strip()
    images = state.get("uploaded_images", [])
    if not api_key:
        return {"error": "API 키가 없어 비전 분석을 실행할 수 없음."}
    if not images:
        return {"error": "교과서 이미지를 업로드해야 비전 분석을 실행할 수 있음."}
    client = create_client(api_key)
    result = call_vision_json(client, state.get("model_name","gpt-4.1"), build_prompt(state), images)
    return {"vision_analysis": result, "error": ""}

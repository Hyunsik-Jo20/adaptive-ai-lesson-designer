from __future__ import annotations
from services.openai_service import create_client, call_json

def node(state: dict) -> dict:
    api_key = state.get("api_key","").strip()
    if not api_key:
        return {"error": "API 키가 없어 학습지를 생성할 수 없음."}
    if not state.get("lesson_plan_output") or not state.get("slides_output"):
        return {"error": "지도안과 슬라이드가 확정되어야 학습지를 생성할 수 있음."}
    prompt = f"""
당신은 초등 학습지 제작 전문가임.
반드시 JSON만 출력할 것.
비전 분석 결과와 수업자 의도를 공동 기초값으로 사용하라.
지도안과 슬라이드를 반영하라.
문제 앞에 multiple_choice 같은 형식명을 쓰지 말라.
학년 수준과 과목 특성을 반영하라.
문항은 가능하면 question_text, supporting_lines, choices, answer_area를 갖는 구조화 객체로 출력하라.

비전 분석:
{state.get("vision_analysis")}

지도안:
{state.get("lesson_plan_output")}

슬라이드:
{state.get("slides_output")}

추가 지침:
{state.get('prompt_settings',{}).get('worksheet','')}

출력 형식:
{{
  "high": {{"questions": []}},
  "middle": {{"questions": []}},
  "low": {{"questions": []}},
  "answers": []
}}
"""
    client = create_client(api_key)
    result = call_json(client, state.get("model_name","gpt-4.1"), prompt)
    return {"worksheet_output": result, "error": ""}

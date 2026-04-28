from __future__ import annotations
from services.openai_service import create_client, call_json

def node(state: dict) -> dict:
    if not state.get("api_key","").strip():
        return {"error": "API 키가 없어 도구 추천을 실행할 수 없음."}
    if not state.get("vision_analysis"):
        return {"error": "비전 분석 결과가 없어 도구 추천을 실행할 수 없음."}

    lesson_input = state.get("lesson_input", {})
    teacher_intent = state.get("teacher_intent", {})
    tools = state.get("reference_data", {}).get("tools", [])

    prompt = f"""
당신은 초등 수업 도구 추천 전문가임.
반드시 JSON만 출력할 것.
비전 분석 결과와 수업자 의도를 공동 기초값으로 사용하라.
같은 도구군을 3개 반복 추천하면 안 됨.
서로 다른 도구 3개를 추천하라.

수업자 의도:
{teacher_intent.get('raw_text','')}

비전 분석:
{state.get("vision_analysis")}

참고 도구 자료:
{tools}

추가 지침:
{state.get('prompt_settings',{}).get('tool','')}

출력 형식:
{{
  "candidates": [
    {{
      "name": "",
      "score_total": 0,
      "score_breakdown": {{}},
      "reason": "",
      "best_for": "",
      "cautions": ""
    }}
  ]
}}
"""
    client = create_client(state["api_key"])
    result = call_json(client, state.get("model_name","gpt-4.1"), prompt)
    return {"tool_recommendation": result, "error": ""}

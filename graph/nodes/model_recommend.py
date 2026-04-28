from __future__ import annotations
from services.openai_service import create_client, call_json

def node(state: dict) -> dict:
    if not state.get("api_key","").strip():
        return {"error": "API 키가 없어 학습모형 추천을 실행할 수 없음."}
    if not state.get("vision_analysis"):
        return {"error": "비전 분석 결과가 없어 학습모형 추천을 실행할 수 없음."}
    selected_tools = state.get("tool_recommendation", {}).get("selected_tools", [])
    if not selected_tools:
        return {"error": "선택 확정된 도구가 없어 학습모형 추천을 실행할 수 없음."}

    prompt = f"""
당신은 초등 학습모형 추천 전문가임.
반드시 JSON만 출력할 것.
비전 분석 결과와 수업자 의도를 공동 기초값으로 사용하라.
선택된 도구를 반영하여 서로 다른 학습모형 3개를 추천하라.

수업자 의도:
{state.get("teacher_intent",{}).get("raw_text","")}

비전 분석:
{state.get("vision_analysis")}

선택 도구:
{selected_tools}

참고 학습모형 자료:
{state.get("reference_data",{}).get("models",[])}

추가 지침:
{state.get('prompt_settings',{}).get('model','')}

출력 형식:
{{
  "candidates": [
    {{
      "name": "",
      "score_total": 0,
      "score_breakdown": {{}},
      "reason": "",
      "phase_names": [],
      "limitations": ""
    }}
  ]
}}
"""
    client = create_client(state["api_key"])
    result = call_json(client, state.get("model_name","gpt-4.1"), prompt)
    return {"model_recommendation": result, "error": ""}

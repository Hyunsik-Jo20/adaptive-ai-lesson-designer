from __future__ import annotations
from services.openai_service import create_client, call_json

def node(state: dict) -> dict:
    api_key = state.get("api_key","").strip()
    if not api_key:
        return {"error": "API 키가 없어 슬라이드를 생성할 수 없음."}
    lesson = state.get("lesson_plan_output")
    if not lesson:
        return {"error": "확정된 지도안이 없어 슬라이드를 생성할 수 없음."}
    prompt = f"""
당신은 수업 슬라이드 설계 전문가임.
반드시 JSON만 출력할 것.
지도안과 비전 분석 결과를 반영하라.
교과서의 실제 문제 상황을 슬라이드에 포함하라.
중복 슬라이드를 만들지 말 것.

비전 분석:
{state.get("vision_analysis")}

지도안:
{lesson}

추가 지침:
{state.get('prompt_settings',{}).get('slides','')}

출력 형식:
{{
  "slides": [
    {{
      "slide_no": 1,
      "title": "",
      "purpose": "",
      "main_content": "",
      "teacher_prompt": "",
      "image_prompt": ""
    }}
  ]
}}
"""
    client = create_client(api_key)
    result = call_json(client, state.get("model_name","gpt-4.1"), prompt)
    return {"slides_output": result, "error": ""}

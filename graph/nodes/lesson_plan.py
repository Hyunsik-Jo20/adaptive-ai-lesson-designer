from __future__ import annotations
from services.openai_service import create_client, call_json

def node(state: dict) -> dict:
    api_key = state.get("api_key","").strip()
    if not api_key:
        return {"error": "API 키가 없어 지도안을 생성할 수 없음."}
    selected_model = state.get("model_recommendation", {}).get("selected_model")
    if not selected_model:
        return {"error": "확정된 학습모형이 없어 지도안을 생성할 수 없음."}
    selected_tools = state.get("tool_recommendation", {}).get("selected_tools", [])
    prompt = f"""
당신은 초등 수업 설계 전문가임.
반드시 JSON만 출력할 것.
비전 분석 결과와 수업자 의도를 공동 기초값으로 사용하라.
단계는 반드시 교수학습모형 단계로 구성하고, 교과서 활동은 단계 내부에 배치하라.
지도안은 개요 / 표 형식 지도안 / 평가 계획 / 피드백 전략 4블록으로 작성하라.
자료 및 유의점에는 오개념 대응, 느린 학생 피드백, 역량, 평가를 포함하라.
교구는 복수 선택과 중복 사용을 허용한다.

수업자 의도:
{state.get("teacher_intent",{}).get("raw_text","")}

비전 분석:
{state.get("vision_analysis")}

선택 도구:
{selected_tools}

선택 학습모형:
{selected_model}

추가 지침:
{state.get('prompt_settings',{}).get('lesson','')}

출력 형식:
{{
  "overview": {{
    "단원": "",
    "차시": "",
    "성취기준": "",
    "학습주제": "",
    "교수·학습모형": "",
    "학습목표": "",
    "수업자 의도": "",
    "핵심개념": "",
    "활용 교구": "",
    "학습문제": ""
  }},
  "lesson_table": [
    {{
      "단계": "",
      "시량": "",
      "교사 활동": "",
      "학생 활동": "",
      "자료 및 유의점": ""
    }}
  ],
  "assessment_plan": [
    {{
      "평가시기": "",
      "평가내용": "",
      "평가방법": "",
      "상": "",
      "중": "",
      "하": ""
    }}
  ],
  "feedback_strategy": [
    {{
      "성취수준": "",
      "평가기준": "",
      "피드백 전략": ""
    }}
  ]
}}
"""
    client = create_client(api_key)
    result = call_json(client, state.get("model_name","gpt-4.1"), prompt)
    return {"lesson_plan_output": result, "error": ""}

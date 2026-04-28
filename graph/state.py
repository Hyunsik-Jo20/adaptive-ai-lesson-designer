from __future__ import annotations
from typing import TypedDict, Any

class AppState(TypedDict, total=False):
    next_action: str
    api_key: str
    model_name: str
    lesson_input: dict[str, Any]
    teacher_intent: dict[str, Any]
    grade_profile: dict[str, Any]
    subject_profile: dict[str, Any]
    reference_data: dict[str, Any]
    uploaded_images: list[str]
    vision_analysis: dict[str, Any]
    tool_recommendation: dict[str, Any]
    model_recommendation: dict[str, Any]
    lesson_plan_output: dict[str, Any]
    slides_output: dict[str, Any]
    worksheet_output: dict[str, Any]
    error: str

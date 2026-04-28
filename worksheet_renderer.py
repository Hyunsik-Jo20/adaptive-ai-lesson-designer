from __future__ import annotations

import re
from typing import Any

import streamlit as st


def normalize_blank(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    for box in ["□", "▢", "◻", "ㅁ"]:
        text = text.replace(box, "(      )")
    return text


def ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, tuple):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def normalize_answer_area(answer_area: dict) -> dict:
    answer_area = dict(answer_area)
    if "placeholder" in answer_area:
        answer_area["placeholder"] = normalize_blank(str(answer_area["placeholder"]))
    if "placeholders" in answer_area:
        answer_area["placeholders"] = [normalize_blank(str(x)) for x in ensure_list(answer_area["placeholders"])]
    return answer_area


def looks_like_support_text(text: str) -> bool:
    if not text:
        return False
    numbers = re.findall(r"\d+", text)
    if len(numbers) >= 2:
        return True
    symbols = ["○", ">", "<", "=", "(      )", "+", ","]
    if any(s in text for s in symbols):
        return True
    if any(s in text for s in ["①", "②", "③", "④"]):
        return True
    return False


def split_support_lines(tail: str) -> list[str]:
    tail = normalize_blank(tail.strip())
    if not tail:
        return []

    if any(mark in tail for mark in ["①", "②", "③", "④"]):
        parts = re.split(r"(?=①|②|③|④)", tail)
        return [p.strip() for p in parts if p.strip()]

    if re.search(r"\(\d+\)", tail):
        parts = re.split(r"(?=\(\d+\))", tail)
        return [p.strip() for p in parts if p.strip()]

    # 여러 수식/비교식이 이어진 경우 줄 분리
    parts = re.split(r"(?=\d{3,4}\s*[=○<>])", tail)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        return parts

    for sep in [" / ", " | ", ";"]:
        if sep in tail:
            return [p.strip() for p in tail.split(sep) if p.strip()]

    return [tail]


def split_question_and_support(text: str) -> tuple[str, list[str]]:
    text = normalize_blank(text.strip())
    if not text:
        return "", []

    if "\n" in text:
        lines = [x.strip() for x in text.split("\n") if x.strip()]
        return lines[0], lines[1:]

    # 선택지 기호가 중간에 나오면 그 앞까지 문제, 뒤는 보기
    choice_match = re.search(r"(①|②|③|④|1\.|\(1\)|ㄱ\.)", text)
    if choice_match:
        idx = choice_match.start()
        before = text[:idx].strip()
        after = text[idx:].strip()
        if len(before) >= 8:
            return before, split_support_lines(after)

    markers = [
        "쓰세요.", "넣으세요.", "고르세요.", "하세요.", "찾으세요.", "찾아보세요.",
        "비교해 보세요.", "나타내어 보세요.", "만들어 보세요.", "써 보세요.", "이어 보세요.",
    ]
    for marker in markers:
        pos = text.find(marker)
        if pos != -1:
            end = pos + len(marker)
            question_text = text[:end].strip()
            tail = text[end:].strip()
            if tail:
                return question_text, split_support_lines(tail)

    m = re.match(r"^(.*?[\.?!])\s+(.+)$", text)
    if m:
        question_text = m.group(1).strip()
        tail = m.group(2).strip()
        if looks_like_support_text(tail):
            return question_text, split_support_lines(tail)

    return text, []


def infer_question_type(question_text: str, support_lines: list[str]) -> str:
    text = f"{question_text} {' '.join(support_lines)}"
    if "알맞은 기호" in text or ("비교" in text and "○" in text):
        return "comparison"
    if "가장 큰 수" in text or "가장 작은 수" in text:
        return "selection"
    if "숫자 카드" in text or "만들" in text:
        return "construction"
    if "바르게 말한" in text or "누구" in text or "고르" in text:
        return "multiple_choice"
    if "자리" in text and ("쓰" in text or "나타내" in text):
        return "decomposition"
    if "왜" in text or "이유" in text or "설명" in text:
        return "explanation"
    return "general"


def normalize_question_object(raw: Any, question_id: int, level: str = "") -> dict:
    if isinstance(raw, dict):
        question_text = raw.get("question_text", raw.get("question", ""))
        support = raw.get("supporting_lines", raw.get("details", raw.get("supporting_text", []))) or []
        choices = raw.get("choices", []) or []
        # dict인데 question 안에 보기까지 붙은 경우 보정
        if not support and not choices and question_text:
            q_text, support = split_question_and_support(str(question_text))
            question_text = q_text
        q = {
            "question_id": raw.get("question_id", question_id),
            "level": raw.get("level", level),
            "question_type": raw.get("question_type", raw.get("type", "general")),
            "question_text": question_text,
            "supporting_lines": support,
            "choices": choices,
            "answer_area": raw.get("answer_area", {}),
            "hint": raw.get("hint", ""),
        }
    else:
        text = str(raw).strip()
        q_text, support = split_question_and_support(text)
        q = {
            "question_id": question_id,
            "level": level,
            "question_type": infer_question_type(q_text, support),
            "question_text": q_text,
            "supporting_lines": support,
            "choices": [],
            "answer_area": {},
            "hint": "",
        }

    q["question_text"] = normalize_blank(q["question_text"])
    q["supporting_lines"] = [normalize_blank(x) for x in ensure_list(q["supporting_lines"])]
    q["choices"] = [normalize_blank(x) for x in ensure_list(q["choices"])]
    q["hint"] = normalize_blank(q.get("hint", ""))
    q["answer_area"] = normalize_answer_area(q["answer_area"]) if isinstance(q.get("answer_area"), dict) else {}
    if q.get("question_type") in ["", "general"]:
        q["question_type"] = infer_question_type(q["question_text"], q["supporting_lines"])
    return q


def render_answer_area(answer_area: dict, q_type: str = "general") -> None:
    if not answer_area:
        if q_type in ["multiple_choice", "selection", "comparison"]:
            st.markdown("<div style='margin-top:14px; margin-left:28px;'>답: (      )</div>", unsafe_allow_html=True)
        elif q_type in ["explanation"]:
            st.markdown("<div style='margin-top:14px; margin-left:28px;'>이유: ________________________________________________</div>", unsafe_allow_html=True)
        return

    area_type = answer_area.get("type", "inline_blank")
    if area_type == "multi_blank":
        placeholders = answer_area.get("placeholders", [])
        st.markdown("<div style='margin-top:14px; margin-left:28px; line-height:2.0;'>", unsafe_allow_html=True)
        for p in placeholders:
            st.markdown(normalize_blank(str(p)))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if area_type == "line":
        label = answer_area.get("label", "답")
        placeholder = answer_area.get("placeholder", "__________________________________")
        st.markdown(f"<div style='margin-top:14px; margin-left:28px;'>{label}: {placeholder}</div>", unsafe_allow_html=True)
        return

    label = answer_area.get("label", "답")
    placeholder = answer_area.get("placeholder", "(      )")
    st.markdown(f"<div style='margin-top:14px; margin-left:28px;'>{label}: {normalize_blank(placeholder)}</div>", unsafe_allow_html=True)


def render_single_question(item: dict, min_height: int = 145) -> None:
    qid = item.get("question_id", "")
    q_text = item.get("question_text", "")
    q_type = item.get("question_type", "general")
    support = ensure_list(item.get("supporting_lines", []))
    choices = ensure_list(item.get("choices", []))
    answer_area = item.get("answer_area", {}) or {}
    hint = item.get("hint", "")

    st.markdown(
        f"""
        <div style="
            min-height:{min_height}px;
            padding: 12px 0 28px 0;
            margin-bottom: 24px;
            border-bottom: 1px dashed #d6d6d6;
        ">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"**{qid}. {q_text}**")

    if support:
        st.markdown("<div style='margin-top:12px; margin-left:28px; line-height:2.0;'>", unsafe_allow_html=True)
        for line in support:
            st.markdown(f"{line}")
        st.markdown("</div>", unsafe_allow_html=True)

    if choices:
        st.markdown("<div style='margin-top:12px; margin-left:28px; line-height:2.0;'>", unsafe_allow_html=True)
        for choice in choices:
            st.markdown(f"{choice}")
        st.markdown("</div>", unsafe_allow_html=True)

    render_answer_area(answer_area, q_type=q_type)
    if hint:
        st.caption(f"힌트: {hint}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_worksheet_items(raw_questions: list[Any], level_label: str = "", min_height: int = 145) -> None:
    if not raw_questions:
        st.info("표시할 문항이 없음.")
        return
    for idx, raw in enumerate(raw_questions, start=1):
        item = normalize_question_object(raw, question_id=idx, level=level_label)
        render_single_question(item, min_height=min_height)

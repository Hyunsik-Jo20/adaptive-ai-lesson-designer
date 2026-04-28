from __future__ import annotations
import os, tempfile
from pathlib import Path
import streamlit as st
import pandas as pd
from services.csv_loader import load_uploaded_csv
from services.profiles import GRADE_PROFILES, SUBJECT_PROFILES
from graph.builder import build_graph
from worksheet_renderer import render_worksheet_items
from export_docx import create_full_docx
from edit_mode_ui import (
    render_edit_mode_toolbar,
    render_readable_table,
    render_editable_table,
    render_save_and_confirm_buttons,
)

st.set_page_config(page_title="학년 적응형 AI 수업설계 지원 도구 v6", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.small-note { color: #666; font-size: 0.92rem; }
.stDataFrame, .stDataEditor { width: 100% !important; }
.wrapped-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.wrapped-table th, .wrapped-table td { border: 1px solid #ddd; padding: 8px 10px; vertical-align: top; white-space: normal; word-break: break-word; }
.wrapped-table th { background: #f6f7fb; }
.worksheet-q { margin: 1.8rem 0 3rem 0; padding: 0.6rem 0 2rem 0; border-bottom: 1px dashed #ddd; min-height: 120px; }
.worksheet-choice { margin-left: 1.8rem; margin-top: 0.55rem; line-height: 1.9; }
.wrapped-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.wrapped-table th, .wrapped-table td { border: 1px solid #ddd; padding: 8px 10px; vertical-align: top; white-space: normal; word-break: break-word; line-height: 1.7; }
.cell-bullets { margin: 0; padding-left: 1.1rem; }
.problem-card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; background: #fff; }
.problem-card h4 { margin: 0 0 10px 0; }
</style>
""", unsafe_allow_html=True)

GRAPH = build_graph()

def init_state():
    ss = st.session_state
    ss.setdefault("api_key", "")
    ss.setdefault("model_name", "gpt-4.1")
    ss.setdefault("lesson_input", {
        "subject": "수학", "grade": "2", "semester": "1", "unit": "",
        "lesson_topic": "", "learning_objectives": "", "curriculum_text": ""
    })
    ss.setdefault("teacher_intent", {"raw_text": "", "is_user_provided": False})
    ss.setdefault("reference_data", {"tools": [], "models": [], "curriculum": []})
    ss.setdefault("uploaded_images", [])
    ss.setdefault("vision_analysis", None)
    ss.setdefault("tool_recommendation", None)
    ss.setdefault("model_recommendation", None)
    ss.setdefault("lesson_plan_output", None)
    ss.setdefault("slides_output", None)
    ss.setdefault("worksheet_output", None)
    ss.setdefault("flags", {
        "vision_confirmed": False,
        "tools_confirmed": False,
        "model_confirmed": False,
        "lesson_confirmed": False,
        "slides_confirmed": False,
    })
    ss.setdefault("show_settings", True)
    ss.setdefault("prompt_settings", {"vision":"", "tool":"", "model":"", "lesson":"", "slides":"", "worksheet":""})
    ss.setdefault("error", "")

def _temp_save(uploaded) -> str:
    suffix = Path(uploaded.name).suffix or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        return tmp.name


def _safe_curriculum_preview(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    preferred = [c for c in ["grade_group", "area", "standard_code", "standard_text", "level_high", "level_mid", "level_low"] if c in df.columns]
    if preferred:
        return df[preferred]
    return df




def _stringify_cell(value):
    if isinstance(value, list):
        return "<br>".join([str(v) for v in value])
    if isinstance(value, dict):
        return "<br>".join([f"<b>{k}</b>: {v}" for k, v in value.items()])
    if value is None:
        return ""
    return str(value).replace("\n", "<br>")


def _render_wrapped_table(df: pd.DataFrame, fixed_cols: dict | None = None):
    if df is None or df.empty:
        st.info("표시할 내용이 없음")
        return
    fixed_cols = fixed_cols or {}
    cols = list(df.columns)
    thead = "".join([f"<th style='width:{fixed_cols.get(col, 'auto')}'>{col}</th>" for col in cols])
    rows = []
    for _, row in df.iterrows():
        tds = "".join([f"<td>{_stringify_cell(row[col])}</td>" for col in cols])
        rows.append(f"<tr>{tds}</tr>")
    html = f"<table class='wrapped-table'><thead><tr>{thead}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


def _normalize_problem_rows(rows):
    normalized = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item["오개념/유의점"] = item.pop("possible_misconceptions", "")
        normalized.append(item)
    return normalized


def _render_problem_blocks(problem_blocks):
    rows = _normalize_problem_rows(problem_blocks)
    if not rows:
        st.info("표시할 문제 블록이 없음")
        return
    field_order = [
        ("instruction", "지시문"),
        ("task_type", "문제 유형"),
        ("given_elements", "제시 자료"),
        ("required_thinking", "요구 사고"),
        ("concepts", "개념"),
        ("teacher_intent", "교사 의도"),
        ("student_action", "학생 행동"),
        ("materials", "자료"),
        ("오개념/유의점", "오개념/유의점"),
    ]
    for row in rows:
        problem_no = row.get("problem_no", "")
        st.markdown(f"<div class='problem-card'><h4>문제 {problem_no}</h4>", unsafe_allow_html=True)
        display_rows = []
        for key, label in field_order:
            if key in row:
                display_rows.append({"항목": label, "내용": row.get(key, "")})
        from edit_mode_ui import render_readable_table
        render_readable_table(display_rows, columns=["항목", "내용"], widths={"항목":"18%","내용":"82%"}, bullet_cols=["내용"])
        st.markdown("</div>", unsafe_allow_html=True)


def _worksheet_split_question_and_support(raw):
    if isinstance(raw, dict):
        question = str(raw.get("question", "")).strip()
        support = []
        choices = raw.get("choices", []) or []
        details = raw.get("details") or raw.get("supporting_text") or []
        if not choices and not details and question:
            import re
            m = re.search(r"(.*?[\.?!]|.*?하세요\.|.*?쓰세요\.|.*?고르세요\.|.*?이어 보세요\.|.*?찾아보세요\.)\s*(.*)", question)
            if m and m.group(2).strip():
                question = m.group(1).strip()
                details = [m.group(2).strip()]
        if isinstance(details, list):
            support.extend([str(x) for x in details if str(x).strip()])
        elif details:
            support.append(str(details))
        return question, [str(c) for c in choices if str(c).strip()], support, raw.get("hint", "")
    text = str(raw).strip()
    if " | " in text:
        parts = [p.strip() for p in text.split(" | ") if p.strip()]
        return parts[0], [], parts[1:], ""
    import re
    m = re.search(r"(.*?(?:\.|\?|!|하세요\.|쓰세요\.|고르세요\.|이어 보세요\.|찾아보세요\.))\s*(.*)", text)
    if m and m.group(2).strip():
        return m.group(1).strip(), [], [m.group(2).strip()], ""
    return text, [], [], ""

def _ensure_list_dict_table(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    for c in df.columns:
        df[c] = df[c].apply(lambda v: "\n".join(map(str, v)) if isinstance(v, list) else v)
    return df

def _subject_profile_name(subject: str) -> str:
    sp = SUBJECT_PROFILES.get(subject, {})
    return sp.get("name") or sp.get("subject") or subject

def _run_step(action: str):
    state = {
        "next_action": action,
        "api_key": st.session_state["api_key"],
        "model_name": st.session_state["model_name"],
        "lesson_input": st.session_state["lesson_input"],
        "teacher_intent": st.session_state["teacher_intent"],
        "grade_profile": GRADE_PROFILES.get(st.session_state["lesson_input"]["grade"], {}),
        "subject_profile": SUBJECT_PROFILES.get(st.session_state["lesson_input"]["subject"], {}),
        "reference_data": st.session_state["reference_data"],
        "uploaded_images": st.session_state["uploaded_images"],
        "vision_analysis": st.session_state.get("vision_analysis"),
        "tool_recommendation": st.session_state.get("tool_recommendation"),
        "model_recommendation": st.session_state.get("model_recommendation"),
        "lesson_plan_output": st.session_state.get("lesson_plan_output"),
        "slides_output": st.session_state.get("slides_output"),
        "worksheet_output": st.session_state.get("worksheet_output"),
        "prompt_settings": st.session_state.get("prompt_settings", {}),
    }
    result = GRAPH.invoke(state)
    for k, v in result.items():
        if k in st.session_state:
            st.session_state[k] = v
        elif k in ["vision_analysis", "tool_recommendation", "model_recommendation", "lesson_plan_output", "slides_output", "worksheet_output", "error"]:
            st.session_state[k] = v

def render_sidebar():
    with st.sidebar:
        st.title("설정")
        st.session_state["api_key"] = st.text_input("OpenAI API Key", value=st.session_state["api_key"], type="password")
        st.session_state["model_name"] = st.text_input("모델", value=st.session_state["model_name"])
        st.markdown("### 엔진 상태")
        st.write("- 워크플로우 엔진: LangGraph 기반")
        st.markdown("### LangGraph 단계별 추가 지침")
        ps = st.session_state["prompt_settings"]
        ps["vision"] = st.text_area("1. 비전 분석 추가 지침", value=ps.get("vision", ""), height=70)
        ps["tool"] = st.text_area("2. 수업도구 추천 추가 지침", value=ps.get("tool", ""), height=70)
        ps["model"] = st.text_area("3. 학습모형 추천 추가 지침", value=ps.get("model", ""), height=70)
        ps["lesson"] = st.text_area("4. 지도안 추가 지침", value=ps.get("lesson", ""), height=70)
        ps["slides"] = st.text_area("5. 슬라이드 추가 지침", value=ps.get("slides", ""), height=70)
        ps["worksheet"] = st.text_area("6. 학습지 추가 지침", value=ps.get("worksheet", ""), height=70)

        st.markdown("### 현재 단계 상태")
        for k, v in st.session_state["flags"].items():
            st.write(f"- {k}: {'완료' if v else '대기'}")

def render_library():
    st.header("참고자료 라이브러리")
    st.caption("수업도구 / 학습모형 / 성취기준 CSV를 업로드함.")
    c1, c2, c3 = st.columns(3)
    for col, title, key in [(c1, "수업도구 CSV", "tools"), (c2, "학습모형 CSV", "models"), (c3, "성취기준 CSV", "curriculum")]:
        with col:
            up = st.file_uploader(title, type=["csv"], key=f"upload_{key}")
            if up and st.button(f"{title} 반영", key=f"btn_{key}"):
                temp = _temp_save(up)
                loaded = load_uploaded_csv(temp)
                if loaded["kind"] == key:
                    st.session_state["reference_data"][key].extend(loaded["records"])
                    st.success(f"{title} 반영 완료")
                    if key == "curriculum":
                        preview = _safe_curriculum_preview(loaded["records"])
                        if not preview.empty:
                            st.markdown("#### 업로드된 성취기준 내용")
                            st.dataframe(preview, use_container_width=True, hide_index=True)
                        else:
                            st.markdown("#### 업로드 원본 미리보기")
                            st.dataframe(loaded.get("dataframe", pd.DataFrame()), use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(pd.DataFrame(loaded["records"]), use_container_width=True, hide_index=True)
                else:
                    st.error(f"이 파일은 {loaded['kind']} 유형으로 인식됨.")
                    st.markdown("#### 업로드 원본 미리보기")
                    st.dataframe(loaded.get("dataframe", pd.DataFrame()), use_container_width=True, hide_index=True)
    st.markdown("### 현재 반영된 자료")
    st.write({
        "도구": len(st.session_state["reference_data"]["tools"]),
        "학습모형": len(st.session_state["reference_data"]["models"]),
        "성취기준": len(st.session_state["reference_data"]["curriculum"]),
    })
    if st.session_state["reference_data"]["curriculum"]:
        st.markdown("#### 성취기준 내용 미리보기")
        df = _safe_curriculum_preview(st.session_state["reference_data"]["curriculum"])
        st.dataframe(df, use_container_width=True, hide_index=True)

def render_input():
    st.header("수업 설계 입력")
    li = st.session_state["lesson_input"]
    gp = GRADE_PROFILES.get(li["grade"], {})
    st.info(f"현재 프로필: {li['grade']}학년 / {li['semester']}학기 / {li['subject']} / 학년대 {gp.get('band','')} / 과목 특화 {_subject_profile_name(li['subject'])}")

    c1, c2, c3, c4 = st.columns(4)
    li["subject"] = c1.selectbox("과목", list(SUBJECT_PROFILES.keys()), index=list(SUBJECT_PROFILES.keys()).index(li["subject"]))
    li["grade"] = c2.selectbox("학년", list(GRADE_PROFILES.keys()), index=list(GRADE_PROFILES.keys()).index(li["grade"]))
    li["semester"] = c3.selectbox("학기", ["1", "2"], index=0 if li["semester"] == "1" else 1)
    li["unit"] = c4.text_input("단원", value=li["unit"])
    li["lesson_topic"] = st.text_input("차시 주제", value=li["lesson_topic"])
    li["learning_objectives"] = st.text_area("학습 목표", value=li["learning_objectives"], height=90)
    st.session_state["teacher_intent"]["raw_text"] = st.text_area("수업자 의도", value=st.session_state["teacher_intent"]["raw_text"], height=110)
    st.session_state["teacher_intent"]["is_user_provided"] = bool(st.session_state["teacher_intent"]["raw_text"].strip())

    if st.session_state["reference_data"]["curriculum"]:
        labels = ["직접 입력"] + [
            f"{r.get('standard_code','')} {r.get('standard_text','')}".strip()
            for r in st.session_state["reference_data"]["curriculum"]
        ]
        chosen = st.selectbox("성취기준 선택", labels)
        if chosen != "직접 입력":
            idx = labels.index(chosen) - 1
            picked = st.session_state["reference_data"]["curriculum"][idx]
            li["curriculum_text"] = picked.get("standard_text","")
            st.write("선택된 성취기준:", picked.get("standard_text",""))
    li["curriculum_text"] = st.text_area("성취기준 내용", value=li["curriculum_text"], height=80)

    uploaded = st.file_uploader("교과서 이미지 업로드(여러 장 가능)", type=["png","jpg","jpeg"], accept_multiple_files=True)
    if uploaded and st.button("이미지 반영"):
        st.session_state["uploaded_images"] = [_temp_save(f) for f in uploaded]
        st.success(f"이미지 {len(st.session_state['uploaded_images'])}장 반영됨.")
    if st.session_state["uploaded_images"]:
        st.caption(f"현재 반영된 이미지 수: {len(st.session_state['uploaded_images'])}")
        st.markdown("#### 반영된 이미지 미리보기")
        cols = st.columns(4)
        for i, img_path in enumerate(st.session_state["uploaded_images"]):
            with cols[i % 4]:
                st.image(img_path, caption=f"이미지 {i+1}", use_container_width=True)

def render_vision():
    st.header("1. 비전 분석")
    if st.button("분석 시작"):
        _run_step("vision")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    out = st.session_state.get("vision_analysis")
    if out:
        st.subheader("차시 해석")
        lesson_df = pd.DataFrame([{"항목": k, "내용": v} for k, v in out.get("lesson_context", {}).items()])
        _render_wrapped_table(lesson_df, {"항목": "22%", "내용": "78%"})

        st.subheader("핵심 개념")
        concepts = out.get("core_concepts", [])
        concept_df = pd.DataFrame({"핵심 개념": concepts}) if concepts else pd.DataFrame()
        _render_wrapped_table(concept_df, {"핵심 개념": "100%"})

        st.subheader("활동 흐름")
        flow_df = _ensure_list_dict_table(out.get("activity_flow", []))
        _render_wrapped_table(flow_df, {"activity_name": "18%", "linked_problem_nos": "12%", "activity_purpose": "25%", "teacher_focus": "22%", "student_focus": "23%"})

        st.subheader("문제 블록")
        problem_blocks = out.get("problem_blocks", [])
        _render_problem_blocks(problem_blocks)
        pb_df = _ensure_list_dict_table(problem_blocks)

        with st.expander("비전 분석 수정", expanded=False):
            st.markdown("##### 차시 해석 수정")
            lesson_edit = st.data_editor(lesson_df, use_container_width=True, hide_index=True, key="vision_lesson_edit")
            st.markdown("##### 핵심 개념 수정")
            concept_edit = st.data_editor(concept_df, use_container_width=True, hide_index=True, key="vision_concept_edit")
            st.markdown("##### 활동 흐름 수정")
            flow_edit = st.data_editor(flow_df, use_container_width=True, hide_index=True, key="vision_flow_edit")
            st.markdown("##### 문제 블록 수정")
            pb_edit = st.data_editor(pb_df, use_container_width=True, hide_index=True, key="vision_pb_edit")
            if st.button("비전 분석 수정 저장"):
                st.session_state["vision_analysis"]["lesson_context"] = {str(r["항목"]): r["내용"] for _, r in lesson_edit.iterrows() if str(r.get("항목", "")).strip()}
                st.session_state["vision_analysis"]["core_concepts"] = [str(x) for x in concept_edit.get("핵심 개념", []).tolist() if str(x).strip()] if not concept_edit.empty else []
                st.session_state["vision_analysis"]["activity_flow"] = flow_edit.to_dict(orient="records")
                st.session_state["vision_analysis"]["problem_blocks"] = pb_edit.to_dict(orient="records")
                st.success("비전 분석 수정 저장 완료")
        if st.button("비전 분석 확인"):
            st.session_state["flags"]["vision_confirmed"] = True
            st.success("비전 분석 확인 완료")

def render_tools():
    st.header("2. 수업도구 추천")
    disabled = not st.session_state["flags"]["vision_confirmed"]
    if st.button("도구 추천하기", disabled=disabled):
        _run_step("tools")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    rec = st.session_state.get("tool_recommendation", {})
    cands = rec.get("candidates", []) if isinstance(rec, dict) else []
    if cands:
        selected = []
        cols = st.columns(len(cands))
        for i, cand in enumerate(cands):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"### {cand.get('name','')}")
                    st.markdown(f"**총점:** {cand.get('score_total','')}")
                    st.markdown(str(cand.get('reason','')))
                    if cand.get("best_for"):
                        st.caption(f"적합 활동: {cand.get('best_for')}")
                    if cand.get("cautions"):
                        st.caption(f"유의점: {cand.get('cautions')}")
                    if st.checkbox("선택", key=f"tool_sel_{i}"):
                        selected.append(cand.get("name",""))
        if st.button("도구 선택 확정"):
            st.session_state["tool_recommendation"]["selected_tools"] = selected
            st.session_state["flags"]["tools_confirmed"] = True
            st.success("도구 선택 확정 완료")

def render_models():
    st.header("3. 학습모형 추천")
    disabled = not st.session_state["flags"]["tools_confirmed"]
    if st.button("학습모형 추천하기", disabled=disabled):
        _run_step("models")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    rec = st.session_state.get("model_recommendation", {})
    cands = rec.get("candidates", []) if isinstance(rec, dict) else []
    if cands:
        cols = st.columns(max(1, len(cands)))
        for i, cand in enumerate(cands):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f"### {cand.get('name','')}")
                    st.markdown(f"**총점:** {cand.get('score_total','')}")
                    st.markdown(str(cand.get('reason','')))
                    if cand.get("phase_names"):
                        st.caption("단계: " + ", ".join(map(str, cand.get("phase_names", []))))
                    if st.button(f"{cand.get('name','')} 선택", key=f"model_{i}"):
                        st.session_state["model_recommendation"]["selected_model"] = cand
        if st.session_state["model_recommendation"].get("selected_model"):
            st.success(f"선택된 모형: {st.session_state['model_recommendation']['selected_model'].get('name','')}")
            if st.button("학습모형 선택 확정"):
                st.session_state["flags"]["model_confirmed"] = True
                st.success("학습모형 선택 확정 완료")

def render_lesson():
    st.header("4. 지도안 작성")
    disabled = not st.session_state["flags"]["model_confirmed"]
    if st.button("지도안 만들기", disabled=disabled):
        _run_step("lesson")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    out = st.session_state.get("lesson_plan_output")
    if out:
        is_edit_mode = render_edit_mode_toolbar("lesson_plan", "지도안")
        tabs = st.tabs(["개요", "표 형식 지도안", "평가 계획", "피드백 전략"])
        with tabs[0]:
            overview_rows = [{"항목": k, "내용": v} for k, v in out.get("overview", {}).items()]
            render_readable_table(overview_rows, columns=["항목", "내용"], height=260)
            if is_edit_mode:
                edited_rows = render_editable_table("overview_rows", overview_rows, columns=["항목", "내용"], height=260)
                save_clicked, _ = render_save_and_confirm_buttons("overview_only", "개요 수정 저장", "개요 점검 확인")
                if save_clicked:
                    st.session_state["lesson_plan_output"]["overview"] = {str(r.get("항목", "")).strip(): r.get("내용", "") for r in edited_rows if str(r.get("항목", "")).strip()}
                    st.success("개요 수정 저장 완료")

        with tabs[1]:
            lesson_columns = ["단계", "시량", "교사 활동", "학생 활동", "자료 및 유의점"]
            if is_edit_mode:
                edited_rows = render_editable_table("lesson_plan_rows", out.get("lesson_table", []), columns=lesson_columns, height=520)
                save_clicked, confirm_clicked = render_save_and_confirm_buttons("lesson_plan", "지도안 수정 저장", "지도안 점검 확인")
                if save_clicked:
                    st.session_state["lesson_plan_output"]["lesson_table"] = edited_rows
                    st.success("지도안 수정 저장 완료")
                if confirm_clicked:
                    st.session_state["flags"]["lesson_confirmed"] = True
                    st.success("지도안 점검 확인 완료")
            else:
                render_readable_table(
                    out.get("lesson_table", []),
                    columns=lesson_columns,
                    height=520,
                    widths={"단계":"13%","시량":"8%","교사 활동":"26%","학생 활동":"23%","자료 및 유의점":"30%"},
                    bullet_cols=["교사 활동", "학생 활동", "자료 및 유의점"],
                )

        with tabs[2]:
            eval_columns = ["평가시기", "평가내용", "평가방법", "평가기준"]
            if is_edit_mode:
                edited_rows = render_editable_table("assessment_rows", out.get("assessment_plan", []), columns=eval_columns, height=320)
                save_clicked, _ = render_save_and_confirm_buttons("assessment_only", "평가 계획 수정 저장", "평가 계획 점검 확인")
                if save_clicked:
                    st.session_state["lesson_plan_output"]["assessment_plan"] = edited_rows
                    st.success("평가 계획 수정 저장 완료")
            else:
                render_readable_table(
                    out.get("assessment_plan", []),
                    columns=eval_columns,
                    height=320,
                    widths={"평가시기":"12%","평가내용":"26%","평가방법":"20%","평가기준":"42%"},
                    bullet_cols=["평가내용", "평가방법", "평가기준"],
                )

        with tabs[3]:
            feedback_columns = ["성취수준", "평가기준", "피드백 전략"]
            if is_edit_mode:
                edited_rows = render_editable_table("feedback_rows", out.get("feedback_strategy", []), columns=feedback_columns, height=320)
                save_clicked, _ = render_save_and_confirm_buttons("feedback_only", "피드백 전략 수정 저장", "피드백 전략 점검 확인")
                if save_clicked:
                    st.session_state["lesson_plan_output"]["feedback_strategy"] = edited_rows
                    st.success("피드백 전략 수정 저장 완료")
            else:
                render_readable_table(
                    out.get("feedback_strategy", []),
                    columns=feedback_columns,
                    height=320,
                    widths={"성취수준":"12%","평가기준":"34%","피드백 전략":"54%"},
                    bullet_cols=["평가기준", "피드백 전략"],
                )

def render_slides():
    st.header("5. 슬라이드")
    disabled = not st.session_state["flags"]["lesson_confirmed"]
    if st.button("슬라이드 만들기", disabled=disabled):
        _run_step("slides")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    out = st.session_state.get("slides_output")
    if out:
        is_edit_mode = render_edit_mode_toolbar("slides", "슬라이드")
        slides_rows = []
        for row in out.get("slides", []):
            if isinstance(row, dict):
                normalized = dict(row)
                normalized["시각화 프롬프트"] = normalized.get("visuals") or normalized.get("image_prompt") or ""
                slides_rows.append(normalized)
        slide_columns = ["slide_no", "title", "purpose", "main_content", "teacher_prompt", "시각화 프롬프트"]
        if is_edit_mode:
            edited_rows = render_editable_table("slides_rows", slides_rows, columns=slide_columns, height=520)
            save_clicked, confirm_clicked = render_save_and_confirm_buttons("slides", "슬라이드 수정 저장", "슬라이드 점검 확인")
            if save_clicked:
                normalized_rows = []
                for row in edited_rows:
                    item = dict(row)
                    item["image_prompt"] = item.get("시각화 프롬프트", "")
                    item["visuals"] = item.get("시각화 프롬프트", "")
                    normalized_rows.append(item)
                st.session_state["slides_output"]["slides"] = normalized_rows
                st.success("슬라이드 수정 저장 완료")
            if confirm_clicked:
                st.session_state["flags"]["slides_confirmed"] = True
                st.success("슬라이드 점검 확인 완료")
        else:
            render_readable_table(
                slides_rows,
                columns=slide_columns,
                height=520,
                widths={"slide_no":"6%","title":"16%","purpose":"16%","main_content":"28%","teacher_prompt":"18%","시각화 프롬프트":"16%"},
                bullet_cols=["main_content", "teacher_prompt", "시각화 프롬프트"],
            )

def render_worksheet():
    st.header("6. 학습지")
    disabled = not st.session_state["flags"]["slides_confirmed"]
    if st.button("학습지 만들기", disabled=disabled):
        _run_step("worksheet")
    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    out = st.session_state.get("worksheet_output")
    if out:
        st.write(f"{st.session_state['lesson_input']['grade']}학년 __반 __번 이름: ________")
        st.subheader(st.session_state["lesson_input"].get("lesson_topic","학습지"))
        tabs = st.tabs(["상", "중", "하", "정답"])
        mapping = [("high","상"), ("middle","중"), ("low","하")]
        for tab, (key, label) in zip(tabs[:3], mapping):
            with tab:
                data = out.get(key, {})
                questions = data.get("questions", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                render_worksheet_items(raw_questions=questions, level_label=label, min_height=145)
        with tabs[3]:
            for a in out.get("answers", []):
                st.write(a)


def render_exports():
    st.header("7. 최종 다운로드")
    st.caption("선택된 교구와 선택된 학습모형만 포함하고, 지도안·슬라이드·학습지는 현재 결과를 그대로 통합함.")
    if st.button("전체 결과 Word 생성"):
        buffer = create_full_docx(st.session_state)
        st.download_button(
            label="Word 파일 다운로드",
            data=buffer,
            file_name="AI_수업설계_결과.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

def main():
    init_state()
    if st.button("설정 보기 / 숨기기"):
        st.session_state["show_settings"] = not st.session_state["show_settings"]
    if st.session_state["show_settings"]:
        render_sidebar()
    st.title("학년 적응형 AI 수업설계 지원 도구 최종본")
    st.caption("워크플로우 엔진: LangGraph 기반 · 단계별 확인/확정 후 다음 단계 진행")
    render_library()
    render_input()
    render_vision()
    render_tools()
    render_models()
    render_lesson()
    render_slides()
    render_worksheet()
    render_exports()

if __name__ == "__main__":
    main()

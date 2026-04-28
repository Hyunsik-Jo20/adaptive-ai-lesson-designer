from __future__ import annotations

from html import escape
from typing import Any, Iterable

import pandas as pd
import streamlit as st

LINE_BREAK = "\n"


def _normalize_multiline_cell(value: Any) -> str:
    """Cell text normalizer: preserves readable line breaks and avoids horizontal overflow."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return LINE_BREAK.join([str(v).strip() for v in value if str(v).strip()])
    if isinstance(value, dict):
        return LINE_BREAK.join(
            [f"{k}: {v}" for k, v in value.items() if str(v).strip()]
        )

    text = str(value).strip()
    if not text:
        return ""

    # Keep existing bullets as line starts.
    text = text.replace("•", f"{LINE_BREAK}• ")

    # Sentence-level line breaks for Korean lesson-plan prose.
    replacements = [
        (". ", f".{LINE_BREAK}"),
        ("다. ", f"다.{LINE_BREAK}"),
        ("함. ", f"함.{LINE_BREAK}"),
        ("임. ", f"임.{LINE_BREAK}"),
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)

    for sep in ["; ", " / ", " | "]:
        text = text.replace(sep, LINE_BREAK)

    lines = [ln.strip() for ln in text.split(LINE_BREAK)]
    return LINE_BREAK.join([ln for ln in lines if ln])


def _bullet_lines(value: Any) -> list[str]:
    text = _normalize_multiline_cell(value)
    if not text:
        return []
    raw_lines = [ln.strip() for ln in text.split(LINE_BREAK) if ln.strip()]
    return [ln[1:].strip() if ln.startswith("•") else ln for ln in raw_lines]


def _coerce_rows_to_df(data: Any, columns: list[str] | None = None) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, list):
        if len(data) == 0:
            df = pd.DataFrame(columns=columns or [])
        elif all(isinstance(x, dict) for x in data):
            df = pd.DataFrame(data)
        else:
            df = pd.DataFrame({(columns[0] if columns else "내용"): list(data)})
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    elif data is None:
        df = pd.DataFrame(columns=columns or [])
    else:
        df = pd.DataFrame({(columns[0] if columns else "내용"): [str(data)]})

    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
    return df


def _dataframe_kwargs(height: int | str | None = None) -> dict:
    kwargs = {
        "use_container_width": True,
        "hide_index": True,
    }
    if height is not None:
        kwargs["height"] = height
    return kwargs


def _cell_to_html(value: Any, *, bullet: bool = False) -> str:
    if bullet:
        items = _bullet_lines(value)
        if not items:
            return ""
        lis = "".join(f"<li>{escape(item)}</li>" for item in items)
        return f"<ul class='cell-bullets'>{lis}</ul>"

    text = _normalize_multiline_cell(value)
    if not text:
        return ""
    return "<br>".join(escape(ln) for ln in text.split(LINE_BREAK) if ln.strip())


def render_edit_toggle(section_key: str, label: str) -> bool:
    state_key = f"{section_key}_edit_mode"
    if state_key not in st.session_state:
        st.session_state[state_key] = False

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"{label} 수정하기", key=f"{section_key}_edit_on"):
            st.session_state[state_key] = True
    with col2:
        if st.button(f"{label} 보기 모드", key=f"{section_key}_edit_off"):
            st.session_state[state_key] = False

    return st.session_state[state_key]


def render_edit_mode_toolbar(section_key: str, label: str) -> bool:
    return render_edit_toggle(section_key, label)


def render_readable_table(
    data: Any,
    columns: list[str] | None = None,
    height: int | str | None = None,
    widths: dict[str, str] | None = None,
    bullet_cols: Iterable[str] | None = None,
    multiline_cols: Iterable[str] | None = None,
):
    """Render a fixed-width HTML table, not st.dataframe, to prevent horizontal scrolling."""
    df = _coerce_rows_to_df(data, columns)
    if df.empty:
        st.info("표시할 내용이 없음.")
        return df

    widths = widths or {}
    bullet_set = set(bullet_cols or [])
    cols = list(df.columns)

    # Fixed layout + wrapping. If height is provided, only vertical scrolling is allowed.
    wrapper_style = "width:100%; overflow-x:hidden;"
    if isinstance(height, int):
        wrapper_style += f" max-height:{height}px; overflow-y:auto;"
    elif height in {"content", "stretch"}:
        wrapper_style += " overflow-y:visible;"

    thead = "".join(
        f"<th style='width:{escape(str(widths.get(col, "auto")))}'>{escape(str(col))}</th>"
        for col in cols
    )

    body_rows: list[str] = []
    for _, row in df.iterrows():
        cells = []
        for col in cols:
            cells.append(
                "<td>" + _cell_to_html(row[col], bullet=(col in bullet_set)) + "</td>"
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    html = f"""
    <div style="{wrapper_style}">
      <table class="wrapped-table">
        <thead><tr>{thead}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    return df


def render_editable_table(
    session_key: str,
    data: Any,
    columns: list[str] | None = None,
    height: int | str | None = None,
):
    df = _coerce_rows_to_df(data, columns)
    edited = st.data_editor(
        df,
        **_dataframe_kwargs(height),
        key=f"{session_key}_editor",
    )
    if isinstance(edited, pd.DataFrame):
        st.session_state[session_key] = edited
        return edited.to_dict(orient="records")
    return data if isinstance(data, list) else []


def render_save_and_confirm_buttons(
    section_key: str,
    save_label: str,
    confirm_label: str,
):
    col1, col2 = st.columns([1, 1])
    save_clicked = False
    confirm_clicked = False

    with col1:
        save_clicked = st.button(save_label, key=f"{section_key}_save")
        if save_clicked:
            st.success("수정 내용이 저장됨.")

    with col2:
        confirm_clicked = st.button(confirm_label, key=f"{section_key}_confirm")

    return save_clicked, confirm_clicked

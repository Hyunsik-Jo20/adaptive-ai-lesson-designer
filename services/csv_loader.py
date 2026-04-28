from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd

def _clean(x: Any) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()

def _read_csv_flex(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    for enc in ["cp949", "utf-8-sig", "utf-8", "euc-kr"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    raise ValueError(f"CSV를 읽을 수 없음: {path}")

def _pick(df: pd.DataFrame, names: list[str]) -> str | None:
    cols = [str(c).strip() for c in df.columns]
    for n in names:
        if n in cols:
            return n
    return None

def load_uploaded_csv(temp_path: str) -> dict:
    df = _read_csv_flex(temp_path)
    tool_col = _pick(df, ["추천 도구", "도구명", "tool_name"])
    model_col = _pick(df, ["교수학습모형", "학습모형", "model_name"])
    standard_col = _pick(df, ["성취기준", "성취기준 내용", "standard_text"])

    if tool_col:
        records = []
        for _, r in df.iterrows():
            records.append({
                "tool_name": _clean(r.get(tool_col)),
                "topic": _clean(r.get(_pick(df, ["학습 주제", "차시 주제", "topic"]))),
                "learning_goal": _clean(r.get(_pick(df, ["수업 목표", "학습 목표", "learning_goal"]))),
                "strengths": _clean(r.get(_pick(df, ["도구 장점", "장점", "strengths"]))),
                "tips": _clean(r.get(_pick(df, ["활용 팁", "유의점", "tips"]))),
                "link": _clean(r.get(_pick(df, ["디지털 도구 링크", "링크", "link"]))),
            })
        return {"kind": "tools", "dataframe": df, "records": records}

    if model_col:
        records = []
        for _, r in df.iterrows():
            records.append({
                "model_name": _clean(r.get(model_col)),
                "concept": _clean(r.get(_pick(df, ["개념", "정의", "concept"]))),
                "principles": _clean(r.get(_pick(df, ["원리", "principles"]))),
                "flow": _clean(r.get(_pick(df, ["수업 흐름", "단계", "flow"]))),
                "good_for": _clean(r.get(_pick(df, ["적용하면 좋은 수업 4가지", "적용 수업", "good_for"]))),
                "notes": _clean(r.get(_pick(df, ["의견", "비고", "notes"]))),
            })
        return {"kind": "models", "dataframe": df, "records": records}

    if standard_col:
        records = []
        for _, r in df.iterrows():
            records.append({
                "standard_code": _clean(r.get(_pick(df, ["성취기준 코드", "standard_code"]))),
                "standard_text": _clean(r.get(standard_col)),
                "level_high": _clean(r.get(_pick(df, ["상", "level_high"]))),
                "level_mid": _clean(r.get(_pick(df, ["중", "level_mid"]))),
                "level_low": _clean(r.get(_pick(df, ["하", "level_low"]))),
                "grade_group": _clean(r.get(_pick(df, ["학년군", "grade_group"]))),
                "area": _clean(r.get(_pick(df, ["영역", "area"]))),
            })
        return {"kind": "curriculum", "dataframe": df, "records": records}

    return {"kind": "unknown", "dataframe": df, "records": []}

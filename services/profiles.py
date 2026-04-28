GRADE_PROFILES = {
    "1": {"band": "1-2", "language_density": "low", "worksheet_types": ["선택형", "연결하기", "빈칸"], "slide_density": "visual_heavy"},
    "2": {"band": "1-2", "language_density": "low", "worksheet_types": ["선택형", "연결하기", "빈칸", "단답형"], "slide_density": "visual_heavy"},
    "3": {"band": "3-4", "language_density": "medium", "worksheet_types": ["선택형", "단답형", "적용형"], "slide_density": "balanced"},
    "4": {"band": "3-4", "language_density": "medium", "worksheet_types": ["선택형", "단답형", "적용형"], "slide_density": "balanced"},
    "5": {"band": "5-6", "language_density": "high", "worksheet_types": ["단답형", "적용형", "짧은서술형"], "slide_density": "content_rich"},
    "6": {"band": "5-6", "language_density": "high", "worksheet_types": ["단답형", "적용형", "짧은서술형"], "slide_density": "content_rich"},
}

SUBJECT_PROFILES = {
    "수학": {"name": "수학", "subject": "수학", "focus": ["문제해결", "비교", "추론", "적용"]},
    "국어": {"name": "국어", "subject": "국어", "focus": ["읽기", "쓰기", "말하기", "듣기"]},
    "사회": {"name": "사회", "subject": "사회", "focus": ["자료해석", "비교", "판단", "적용"]},
    "과학": {"name": "과학", "subject": "과학", "focus": ["관찰", "탐구", "실험", "해석"]},
}

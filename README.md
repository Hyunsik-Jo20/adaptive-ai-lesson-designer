# 학년 적응형 AI 수업설계 지원 도구 최종본

## 실행 방법

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 포함된 최종 기능

- LangGraph 기반 단계형 수업 설계 흐름 유지
- 비전 분석 결과 + 수업자 의도 공동 기초값 유지
- 설정창에서 LangGraph 단계별 추가 지침 입력 가능
- 자료 라이브러리 CSV 업로드
- 교과서 이미지 업로드 및 미리보기
- 수업도구/학습모형 선택 확정 후 다음 단계 진행
- 지도안/슬라이드 수정 모드 및 점검 확인
- 학습지 문항 구조화 렌더링
- 전체 결과 Word 다운로드
- HWPX 변환 시도 버튼

## HWPX 참고

HWPX 변환은 PC에 pandoc 또는 pypandoc-hwpx 계열 변환 도구가 설치되어 있어야 작동할 수 있음. 변환이 실패할 경우 Word 파일을 내려받아 한글에서 열고 HWPX로 저장하는 방식을 권장함.

# 학년 적응형 AI 수업설계 지원 도구 최종본

## 실행 방법

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 포함된 최종 기능

- OpenAI api키를 직접 발급받으셔서 좌측 상단에 Key 입력창에 입력하셔야 됩니다.
- LangGraph 기반 단계형 수업 설계 흐름 유지
- 비전 분석 결과 + 수업자 의도 공동 기초값 유지
- 설정창에서 LangGraph 단계별 추가 지침 입력 가능
- 자료 라이브러리 CSV 업로드
- 교과서 이미지 업로드 및 미리보기
- 수업도구/학습모형 선택 확정 후 다음 단계 진행
- 지도안/슬라이드 수정 모드 및 점검 확인
- 학습지 문항 구조화 렌더링
- 전체 결과 Word 다운로드

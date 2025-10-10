# intent_classifier.py

from keywords import VICTIM_TYPE_KEYWORDS, CRISIS_KEYWORDS

class IntentClassifier:
    def __init__(self):
        self.intent_keywords = VICTIM_TYPE_KEYWORDS
        self.crisis_keywords = CRISIS_KEYWORDS

    def is_crisis(self, text: str) -> bool:
        """
        위기 키워드가 포함되었는지 확인
        """
        return any(word in text for word in self.crisis_keywords)

    def classify(self, text: str):
        """
        사용자 입력 → 의도 분류
        1. 위기 상황 우선 체크
        2. 피해 유형 감지 (경매/보증금미반환/신탁사기/조세채권)
        3. 일반 대화
        """
        # 1. 위기 상황 최우선
        if self.is_crisis(text):
            return 'crisis', 1.0

        # 2. 피해 유형 점수 계산
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            match_count = sum(1 for kw in keywords if kw in text)
            scores[intent] = match_count

        # 3. 점수 제일 높은 의도 선택
        top_label = max(scores, key=scores.get)
        if scores[top_label] > 0:
            confidence = scores[top_label] / len(self.intent_keywords[top_label])
            return top_label, confidence

        # 4. 일반 대화 (분류 안됨)
        return 'general', 0.0

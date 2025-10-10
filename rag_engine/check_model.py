import google.generativeai as genai

# 여기에 API 키 입력
GOOGLE_API_KEY = "AIzaSyDjuU6nT4Avn51DnTH21DXnhLaor8t-SgI"

genai.configure(api_key=GOOGLE_API_KEY)

print("사용 가능한 Gemini 모델 목록:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   설명: {model.display_name}")
        print()

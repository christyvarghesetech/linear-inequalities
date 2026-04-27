from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
print(f"Key format valid: {bool(api_key and api_key != 'your_gemini_api_key_here')}")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hi"
    )
    print("Success:", response.text)
except Exception as e:
    print("Exception details:", repr(e))

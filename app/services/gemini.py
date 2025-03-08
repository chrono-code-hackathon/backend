from langchain_google_genai import ChatGoogleGenerativeAI

def get_gemini_response(prompt: str) -> str:
    chat = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.5)
    return chat.invoke(prompt)
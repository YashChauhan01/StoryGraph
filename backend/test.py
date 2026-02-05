import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# 1. Load variables from your .env file
load_dotenv()

# 2. Initialize the Llama 3.1 model via Groq
# Ensure your .env has GROQ_API_KEY=gsk_...
try:
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )

    print("🚀 Sending request to Groq...")
    
    # 3. Invoke the model
    response = llm.invoke("Identify the character: Antonio, a merchant of Venice.")
    
    print("\n✅ AI Response:")
    print(response.content)

except Exception as e:
    print(f"\n❌ Error connecting to Groq: {e}")
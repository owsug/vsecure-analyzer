import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

def get_gpt_recommendation(message: str, code: str, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "explanation": "No OpenAI API key provided.",
            "fix": ""
        }

    openai.api_key = api_key

    prompt = (
        "You are a security expert AI assistant. Given the following security issue description and code, "
        "explain clearly why it's insecure, and suggest a secure fix.\n\n"
        f"Issue:\n{message}\n\n"
        f"Code:\n{code}\n\n"
        "Respond with:\n"
        "Explanation:\n<your explanation>\n\nFix:\n<your fixed version of the code>\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content
        explanation_part = content.split("Explanation:")[-1].split("Fix:")[0].strip()
        fix_part = content.split("Fix:")[-1].strip()

        return {
            "explanation": explanation_part,
            "fix": fix_part
        }

    except Exception as e:
        print("GPT error:", str(e))
        return {
            "explanation": "Failed to generate explanation.",
            "fix": ""
        }

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

def get_gpt_fix(message: str, code: str, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"explanation": "No OpenAI API key provided.", "fixedCode": ""}

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are a security expert AI assistant."
        " Given the following insecure code snippet, generate only the fixed version of the code"
        " without explanation, markdown, or comments. Do not include any other text."
        "\n\nIssue:\n" + message + "\n\n"
        "Code:\n" + code + "\n\n"
        "Respond with only the fixed code."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        return {
            "explanation": message,
            "fixedCode": content
        }

    except Exception as e:
        print("[analyzer-server] GPT error:", str(e))
        return {"explanation": "GPT request failed.", "fixedCode": ""}

def get_gpt_recommendation(message: str, code: str, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"explanation": "No OpenAI API key provided.", "fixedCode": ""}

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are a security expert AI assistant."
        " Analyze the following code and explain clearly what the vulnerability is,"
        " and suggest a secure fix."
        " Focus on clarity, without markdown or code blocks."
        "\n\nIssue:\n" + message + "\n\n"
        "Code:\n" + code + "\n\n"
        "Respond with:\nExplanation: <why it's insecure>\nFixedCode: <corrected version>"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()

        explanation = ""
        fixed_code = ""

        if "Explanation:" in content:
            explanation = content.split("Explanation:")[-1].split("FixedCode:")[0].strip()
        if "FixedCode:" in content:
            fixed_code = content.split("FixedCode:")[-1].strip()

        return {
            "explanation": explanation or message,
            "fixedCode": fixed_code
        }

    except Exception as e:
        print("[analyzer-server] GPT error:", str(e))
        return {"explanation": "GPT request failed.", "fixedCode": ""}

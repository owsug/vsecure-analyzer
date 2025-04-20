from openai import OpenAI
import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

def get_gpt_recommendation(message: str, full_code: str, line: int, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"explanation": "No API key.", "fixedCode": ""}

    client = OpenAI(api_key=api_key)

    explanation_prompt = (
        "You are a security expert AI assistant.\n"
        "Given the following full file code and a vulnerability at the specified line number,\n"
        "explain why it is a vulnerability and suggest how to fix it.\n\n"
        f"Vulnerability Line: {line}\n"
        f"Issue Description: {message}\n\n"
        f"Code:\n{full_code}\n\n"
        "Explanation:"
    )

    fix_prompt = (
        "You are a security expert AI assistant.\n"
        "Given the following full code and a vulnerability at the specified line,\n"
        "respond ONLY with the corrected version of the entire file.\n"
        "Do not include any explanation, formatting, or markdown.\n\n"
        f"Vulnerability Line: {line}\n"
        f"Issue: {message}\n\n"
        f"Code:\n{full_code}\n\n"
        "Fixed Code:\n"
    )

    try:
        explanation_res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": explanation_prompt}],
            temperature=0.3
        )
        explanation = explanation_res.choices[0].message.content.strip()
    except Exception as e:
        print("[gpt_assistant] Explanation error:", str(e))
        explanation = "GPT explanation failed."

    try:
        fix_res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": fix_prompt}],
            temperature=0.2
        )
        fixed_code = fix_res.choices[0].message.content.strip()
    except Exception as e:
        print("[gpt_assistant] Fix error:", str(e))
        fixed_code = ""

    print("[gpt_assistant] GPT explanation + fix ready.")
    return {
        "explanation": explanation,
        "fixedCode": fixed_code
    }


def get_gpt_explanation(message: str, code: str, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"explanation": "No API key.", "fixedCode": ""}
    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a security expert AI assistant. Given the following issue description and code snippet, explain clearly and concisely why it's a vulnerability."
        f"\n\nIssue:\n{message}\n\nCode:\n{code}\n\nExplanation:"
    )
    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        print("[gpt_assistant] GPT response:", res.choices[0].message.content)
        return {"explanation": res.choices[0].message.content.strip(), "fixedCode": ""}
    except Exception as e:
        print("[gpt_assistant] Explanation error:", str(e))
        return {"explanation": "GPT explanation failed.", "fixedCode": ""}

def get_gpt_fix(message: str, code: str, user_api_key: str = "") -> Dict:
    api_key = user_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"fixedCode": ""}
    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a security expert AI assistant. Given the following issue description and code, "
        "respond ONLY with the corrected version of the code. Do not include any explanation, markdown, or formatting. "
        "Respond with ONLY the code.\n\n"
        f"Issue:\n{message}\n\n"
        f"Code:\n{code}\n\n"
        "FixedCode:\n"
    )
    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        print("[gpt_assistant] GPT response:", res.choices[0].message.content)
        return {"fixedCode": res.choices[0].message.content.strip()}
    except Exception as e:
        print("[gpt_assistant] Fix error:", str(e))
        return {"fixedCode": ""}

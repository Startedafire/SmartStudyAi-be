import os, json, requests, re

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3.1:free"


def _clean_json_output(content: str) -> str:
    """Remove markdown fences and clean JSON text."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
    return cleaned


def _validate_quiz_structure(quiz: dict) -> dict:
    """
    Ensure quiz JSON follows tree structure.
    - Must have "quiz" → "questions"
    - Each question must have id, question, options[], and answer
    - Options must have ids A–D
    - If missing/invalid, fix minimally
    """
    validated = {"quiz": {"title": "Generated Quiz", "questions": []}}

    if not isinstance(quiz, dict):
        return validated

    qroot = quiz.get("quiz") or {}
    questions = qroot.get("questions", [])
    if not isinstance(questions, list):
        return validated

    for idx, q in enumerate(questions, start=1):
        question_text = q.get("question") if isinstance(q, dict) else None
        options = q.get("options") if isinstance(q, dict) else []
        answer = q.get("answer") if isinstance(q, dict) else None

        # Ensure options are valid
        fixed_options = []
        if isinstance(options, list):
            for opt_idx, opt in enumerate(options):
                if isinstance(opt, dict):
                    oid = opt.get("id") or chr(65 + opt_idx)  # A, B, C...
                    otext = opt.get("text") or f"Option {oid}"
                    fixed_options.append({"id": oid, "text": otext})
        # Ensure at least 2 options
        while len(fixed_options) < 2:
            oid = chr(65 + len(fixed_options))
            fixed_options.append({"id": oid, "text": f"Option {oid}"})

        # Validate answer
        valid_ids = {opt["id"] for opt in fixed_options}
        if answer not in valid_ids:
            answer = fixed_options[0]["id"]

        validated["quiz"]["questions"].append({
            "id": idx,
            "question": question_text or f"Untitled Question {idx}",
            "options": fixed_options,
            "answer": answer
        })

    return validated


def generate_questions(notes_text: str, num_questions: int = 5) -> dict:
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    prompt = f"""
    Generate {num_questions} multiple-choice questions from these notes:
    {notes_text}

    Format the response as valid JSON with this structure:

    {{
      "quiz": {{
        "title": "Generated Quiz",
        "questions": [
          {{
            "id": <number>,
            "question": <string>,
            "options": [
              {{ "id": "A", "text": <string> }},
              {{ "id": "B", "text": <string> }},
              {{ "id": "C", "text": <string> }},
              {{ "id": "D", "text": <string> }}
            ],
            "answer": <string of correct option id>
          }}
        ]
      }}
    }}
    """

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a quiz generator. Output only JSON, no commentary."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    cleaned = _clean_json_output(content)

    try:
        parsed = json.loads(cleaned)
        return _validate_quiz_structure(parsed)
    except Exception:
        # Fallback: return empty quiz with raw content for debugging
        return {
            "quiz": {
                "title": "Generated Quiz",
                "questions": [],
                "raw": content
            }
        }

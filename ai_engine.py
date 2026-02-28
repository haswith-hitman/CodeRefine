"""
CodeRefine — AI Engine
Uses llama-3.3-70b-versatile via Groq — fast, accurate, great JSON output.

API KEY SETUP
─────────────
Set your Groq API key as an environment variable before running:

  Option 1 — .env file (recommended):
      Create a file named  .env  next to this file and add:
          GROQ_API_KEY=gsk_your_key_here

  Option 2 — shell export:
      export GROQ_API_KEY=gsk_your_key_here

  Option 3 — Windows cmd:
      set GROQ_API_KEY=gsk_your_key_here

Get your free key at: https://console.groq.com
"""

import json
import os
import re

# ── Load .env if python-dotenv is installed (optional but convenient) ─────────
try:
    from dotenv import load_dotenv
    # Try loading from several possible locations
    _base = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_base, ".env"), override=False)
    load_dotenv(os.path.join(os.getcwd(), ".env"), override=False)
except ImportError:
    pass  # dotenv not installed — rely on shell env vars

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL = "llama-3.3-70b-versatile"


def _get_client():
    """Return a fresh Groq client using GROQ_API_KEY from the environment."""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError(
            "The 'groq' package is not installed.\n"
            "Run: pip install groq"
        )

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY environment variable is not set.\n"
            "1. Go to https://console.groq.com and get your free API key.\n"
            "2. Create a file named .env in the same folder as this script.\n"
            "3. Add this line to it:  GROQ_API_KEY=gsk_your_key_here\n"
            "4. Restart the app."
        )
    return Groq(api_key=api_key)


# ── Core API call ─────────────────────────────────────────────────────────────

def _call(system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> str:
    """Single Groq API call with system + user messages. Returns text."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=0.95,
        stream=False,
    )
    return resp.choices[0].message.content or ""


# ── JSON extraction ───────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Find and extract the outermost { ... }
    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response. Got: {text[:300]}")

    depth, end = 0, start
    in_str, esc = False, False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    raw = text[start:end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt a lenient repair: remove control characters
        raw_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
        return json.loads(raw_clean)


# ── Public API ────────────────────────────────────────────────────────────────

def review_code(code: str, language: str, context: str = "") -> dict:
    """
    Deep code review. Returns:
        summary, complexity, confidence, perf_score, quality_verdict,
        bugs, performance, security, best_practices
    """
    ctx = f"\n\nADDITIONAL CONTEXT: {context}" if context else ""

    system = (
        f"You are a world-class {language} code reviewer with deep expertise in "
        "security, performance, and correctness. "
        "You MUST respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )

    user = f"""Perform a thorough code review of the {language} code below and return a JSON object.{ctx}

ANALYSIS RULES — follow strictly:
- Reference actual variable/function names from the code in every finding
- For each bug: explain exactly what breaks at runtime and when
- For each security issue: describe the real attack vector for this specific code
- If a category has no real issues, return an empty array — never fabricate findings
- Scores must honestly reflect code quality (don't default to 50/60/80)

Return ONLY this JSON structure:
{{
  "summary": "2-3 sentences: what this code does + honest overall quality assessment",
  "complexity": <integer 0-100, cyclomatic complexity estimate>,
  "confidence": <integer 0-100, confidence in this review>,
  "perf_score": <integer 0-100, 100 = perfectly optimal>,
  "quality_verdict": "excellent|good|needs_work|poor",
  "bugs": [
    {{
      "title": "name of the specific bug",
      "description": "exactly what is broken and what runtime consequence occurs",
      "line_hint": "function name or code fragment where this occurs",
      "fix": "corrected code snippet or precise fix steps",
      "severity": "critical|high|medium|low"
    }}
  ],
  "performance": [
    {{
      "title": "performance issue name",
      "description": "specific inefficiency referencing the actual code",
      "suggestion": "optimized version or approach with example",
      "impact": "e.g. O(n²) → O(n) or eliminates redundant DB query"
    }}
  ],
  "security": [
    {{
      "title": "vulnerability name",
      "description": "exact attack vector and impact for this code",
      "cve_type": "e.g. SQL Injection / XSS / Path Traversal / Hardcoded Secret",
      "fix": "concrete remediation with code",
      "severity": "critical|high|medium|low"
    }}
  ],
  "best_practices": [
    {{
      "title": "practice name",
      "description": "specific violation in this code",
      "reference": "e.g. PEP 8 / OWASP Top 10 / Clean Code",
      "example": "short improved code example"
    }}
  ]
}}

{language} code:
```{language}
{code}
```"""

    text = _call(system, user, temperature=0.15, max_tokens=4096)
    try:
        data = _extract_json(text)
        data.setdefault("summary", "Analysis complete.")
        data.setdefault("complexity", 50)
        data.setdefault("confidence", 75)
        data.setdefault("perf_score", 60)
        data.setdefault("quality_verdict", "needs_work")
        for k in ("bugs", "performance", "security", "best_practices"):
            if not isinstance(data.get(k), list):
                data[k] = []
        return data
    except Exception as e:
        return {
            "summary": f"⚠️ Could not parse review response. Error: {e}. Raw: {text[:300]}",
            "complexity": 50, "confidence": 50, "perf_score": 50,
            "quality_verdict": "needs_work",
            "bugs": [], "performance": [], "security": [], "best_practices": [],
            "_raw": text[:500],
        }


def rewrite_code(code: str, language: str) -> dict:
    """
    Rewrites code to production quality.
    Returns: rewritten_code, improvements, orig/rw time/space complexity
    """
    system = (
        f"You are a principal {language} engineer. "
        f"You write production-grade, idiomatic {language}. "
        "Respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )

    user = f"""Rewrite the {language} code below to be production-ready and return JSON.

REWRITE REQUIREMENTS:
1. Correct every bug — rewritten code MUST be functionally correct
2. Choose the best algorithm and data structures for performance
3. Secure all inputs; handle errors, edge cases, and boundary conditions
4. Use idiomatic {language}: proper naming, type hints/annotations, meaningful comments
5. The "rewritten_code" value must be the COMPLETE runnable file/function — no truncation

Return ONLY this JSON:
{{
  "orig_time_complexity": "Big-O of original e.g. O(n²)",
  "orig_space_complexity": "Big-O space of original e.g. O(n)",
  "rw_time_complexity": "Big-O of rewritten e.g. O(n log n)",
  "rw_space_complexity": "Big-O space of rewritten e.g. O(1)",
  "rewritten_code": "COMPLETE rewritten {language} code — must be runnable",
  "improvements": [
    {{
      "category": "Performance|Security|Readability|Bug Fix|Best Practice",
      "title": "what changed (be specific)",
      "description": "exact change and why it was made",
      "impact": "concrete benefit e.g. prevents crash on empty list"
    }}
  ]
}}

Original {language} code:
```{language}
{code}
```"""

    text = _call(system, user, temperature=0.1, max_tokens=4096)
    try:
        data = _extract_json(text)
        data.setdefault("rewritten_code", code)
        if not isinstance(data.get("improvements"), list):
            data["improvements"] = []
        data.setdefault("orig_time_complexity", "O(n)")
        data.setdefault("orig_space_complexity", "O(n)")
        data.setdefault("rw_time_complexity", "O(n)")
        data.setdefault("rw_space_complexity", "O(n)")
        return data
    except Exception as e:
        return {
            "rewritten_code": code, "improvements": [],
            "orig_time_complexity": "O(n)", "orig_space_complexity": "O(n)",
            "rw_time_complexity": "O(n)", "rw_space_complexity": "O(n)",
            "_error": str(e),
        }


def explain_code(code: str, language: str) -> str:
    """Return a structured plain-English explanation of the code."""
    system = "You are a senior developer who explains code clearly to both beginners and experts."
    user = f"""Explain this {language} code clearly using this structure:

**Purpose** — What problem does this code solve?
**How it works** — Step-by-step walkthrough referencing actual function/variable names
**Inputs & Outputs** — What goes in and comes out, including types and shapes
**Edge Cases & Gotchas** — Potential issues, assumptions, surprising behavior

{language} code:
```{language}
{code}
```"""
    return _call(system, user, temperature=0.3, max_tokens=2048)


def translate_code(code: str, source_lang: str, target_lang: str) -> dict:
    """Translate code between languages with idiomatic output."""
    system = (
        f"You are an expert polyglot engineer fluent in {source_lang} and {target_lang}. "
        "Respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )
    user = f"""Translate this {source_lang} code to idiomatic {target_lang} and return JSON.

RULES:
- Write idiomatic {target_lang} — NOT a literal line-by-line translation
- Use the best {target_lang} stdlib/libraries for the task
- Apply {target_lang} naming conventions
- Preserve exact logic and edge case behavior
- Add all required imports

Return ONLY this JSON:
{{
  "translated_code": "complete idiomatic {target_lang} code",
  "notes": "2-3 sentences on key translation decisions",
  "idiom_changes": [
    {{"original": "what in {source_lang}", "translated": "what in {target_lang}", "reason": "why"}}
  ],
  "warnings": "behavioral differences or limitations, or empty string"
}}

{source_lang} code:
```{source_lang}
{code}
```"""

    text = _call(system, user, temperature=0.2, max_tokens=4096)
    try:
        data = _extract_json(text)
        data.setdefault("translated_code", code)
        data.setdefault("notes", "Translation complete.")
        if not isinstance(data.get("idiom_changes"), list):
            data["idiom_changes"] = []
        data.setdefault("warnings", "")
        return data
    except Exception as e:
        return {
            "translated_code": code,
            "notes": f"Translation response could not be parsed. Error: {e}",
            "idiom_changes": [],
            "warnings": text[:400],
        }


def generate_challenge(language: str, difficulty: str, topic: str) -> dict:
    """Generate a coding challenge with starter code, hints, and solution."""
    system = (
        f"You are a coding challenge designer specializing in {language}. "
        "Respond with a single valid JSON object only."
    )
    user = f"""Create a {difficulty} {language} coding challenge on '{topic}'.

Return ONLY this JSON:
{{
  "title": "concise challenge title",
  "description": "clear problem statement with 1-2 concrete examples showing input → output",
  "constraints": ["constraint e.g. 1 <= n <= 10^5", "time limit note"],
  "starter_code": "starter {language} template with TODO markers",
  "hints": ["algorithmic hint 1 (no spoilers)", "hint 2", "hint 3"],
  "solution": "complete correct commented {language} solution",
  "test_cases": [
    {{"input": "concrete input", "expected": "expected output", "explanation": "why"}}
  ],
  "time_complexity": "expected optimal Big-O",
  "tags": ["tag1", "tag2"]
}}"""

    text = _call(system, user, temperature=0.6, max_tokens=2048)
    try:
        data = _extract_json(text)
        data.setdefault("title", "Coding Challenge")
        data.setdefault("description", "Solve the problem.")
        data.setdefault("starter_code", f"# Write your {language} solution here\n")
        if not isinstance(data.get("hints"), list):
            data["hints"] = []
        data.setdefault("solution", "")
        if not isinstance(data.get("test_cases"), list):
            data["test_cases"] = []
        if not isinstance(data.get("constraints"), list):
            data["constraints"] = []
        data.setdefault("time_complexity", "O(n)")
        if not isinstance(data.get("tags"), list):
            data["tags"] = []
        return data
    except Exception as e:
        return {
            "title": "Challenge", "description": text[:400],
            "starter_code": f"# {language} solution\n",
            "hints": [], "solution": "", "test_cases": [],
            "constraints": [], "time_complexity": "O(n)", "tags": [],
            "_error": str(e),
        }


def analyze_code_dna(code: str, language: str) -> dict:
    """
    Analyzes code and returns a developer DNA profile.
    Strictly evidence-based — every finding must quote actual code from the input.
    """
    system = (
        "You are an expert code analyst who builds developer personality profiles strictly from "
        "observable patterns in the submitted code. "
        "CRITICAL RULES: "
        "1. Every gene score, superpower, and blind spot MUST be based ONLY on what is literally present in the code. "
        "2. If the code has no comments, score Comment Density as 0-15. "
        "3. If the code has no error handling (no try/except/catch), score Error Handling as 0-20. "
        "4. If the code is short/simple, scores should reflect simplicity — do NOT invent complexity. "
        "5. Never give high scores for traits that are absent from the code. "
        "6. Evidence field must quote an actual variable name, function name, or line from the code. "
        "Respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )

    # Pre-analyze some concrete metrics to feed into the prompt
    lines = code.strip().split('\n')
    total_lines = len(lines)
    comment_lines = sum(1 for l in lines if l.strip().startswith(('#', '//', '*', '/*', '"""', "'''")))
    has_try = 'try' in code or 'catch' in code or 'except' in code
    has_types = '->' in code or ': int' in code or ': str' in code or ': list' in code or ': dict' in code
    magic_numbers = len(re.findall(r'\b(?<!\w)(?!0\b)(?!1\b)\d{2,}\b', code))
    func_count = len(re.findall(r'\bdef \w+|\bfunction \w+|\bfunc \w+', code))
    todo_count = code.upper().count('TODO') + code.upper().count('FIXME') + code.upper().count('HACK')

    user = f"""Analyze this {language} code and produce a Developer DNA profile.

OBJECTIVE CODE METRICS (use these as ground truth for your scores):
- Total lines: {total_lines}
- Comment lines: {comment_lines} ({round(comment_lines/max(total_lines,1)*100)}% of code)
- Has error handling (try/catch/except): {has_try}
- Has type annotations: {has_types}
- Magic numbers detected: {magic_numbers}
- Function/method count: {func_count}
- TODO/FIXME/HACK markers: {todo_count}

SCORING RULES — follow exactly:
- Comment Density score: {min(100, int(comment_lines/max(total_lines,1)*100*3))} (derived from actual comment ratio)
- Error Handling score: {"60-80 if error handling is thorough, 20-40 if minimal, 0-15 if absent" if has_try else "0-15 (NO try/catch/except found in code)"}
- Type Safety score: {"50-85 based on how consistently types are used" if has_types else "0-20 (NO type annotations found)"}
- Magic Numbers score (lower = more magic numbers): {max(0, 90 - magic_numbers*15)}

For ALL other genes: base scores STRICTLY on observable patterns in the code below.

Return ONLY this JSON (genes array must have EXACTLY 7 entries):
{{
  "archetype": "ONE of exactly: The Defensive Architect / The Speed Demon / The Perfectionist / The Pragmatist / The Academic / The Cowboy / The Minimalist / The Over-Engineer",
  "archetype_desc": "2-3 sentences — reference specific function names, variable names, or patterns from the actual code",
  "archetype_icon": "single emoji",
  "summary": "3 honest sentences about this developer's style — each sentence must reference something specific from the code",
  "genes": [
    {{"trait": "Error Handling",    "score": <0-100 per rules above>, "label": "descriptor", "evidence": "exact function/variable/pattern from code or 'Not present in submitted code'"}},
    {{"trait": "Naming Clarity",    "score": <0-100>, "label": "descriptor", "evidence": "quote actual variable or function name from code"}},
    {{"trait": "Comment Quality",   "score": <0-100 per rules above>, "label": "descriptor", "evidence": "quote actual comment or state 'No comments in code'"}},
    {{"trait": "Code Modularity",   "score": <0-100>, "label": "descriptor", "evidence": "reference actual structure from code"}},
    {{"trait": "Type Safety",       "score": <0-100 per rules above>, "label": "descriptor", "evidence": "quote type annotation or state 'No type annotations found'"}},
    {{"trait": "Complexity Control","score": <0-100>, "label": "descriptor", "evidence": "reference actual nesting/logic from code"}},
    {{"trait": "Code Cleanliness",  "score": <0-100>, "label": "descriptor", "evidence": "specific observation from the actual code"}}
  ],
  "superpowers": [
    {{"title": "name", "desc": "based on ACTUAL strength visible in the code — quote the evidence", "icon": "emoji"}},
    {{"title": "name", "desc": "based on ACTUAL strength visible in the code — quote the evidence", "icon": "emoji"}}
  ],
  "blind_spots": [
    {{"title": "name", "desc": "based on what is ACTUALLY MISSING or weak in the code — be specific", "icon": "emoji"}},
    {{"title": "name", "desc": "based on what is ACTUALLY MISSING or weak in the code — be specific", "icon": "emoji"}}
  ],
  "compatibility_tags": ["tag reflecting actual code style", "tag2", "tag3"],
  "works_well_with": "developer type that complements the weaknesses actually seen in this code",
  "clashes_with": "developer type that conflicts with the style actually seen in this code",
  "famous_developer_match": "real famous developer name + one-line reason based on actual code patterns",
  "dna_score": <integer 0-100: honest weighted average of all 7 gene scores>
}}

{language} code to analyze:
```{language}
{code}
```"""

    text = _call(system, user, temperature=0.2, max_tokens=3500)
    try:
        data = _extract_json(text)
        # Validate and clamp all gene scores
        genes = data.get("genes", [])
        if not isinstance(genes, list):
            genes = []
        for g in genes:
            g["score"] = max(0, min(100, int(g.get("score", 50))))
        data["genes"] = genes
        # Recompute dna_score as honest average of gene scores
        if genes:
            data["dna_score"] = round(sum(g["score"] for g in genes) / len(genes))
        data.setdefault("archetype", "The Pragmatist")
        data.setdefault("archetype_desc", "Analysis complete.")
        data.setdefault("archetype_icon", "🧬")
        data.setdefault("summary", "")
        data.setdefault("superpowers", [])
        data.setdefault("blind_spots", [])
        data.setdefault("compatibility_tags", [])
        data.setdefault("works_well_with", "")
        data.setdefault("clashes_with", "")
        data.setdefault("famous_developer_match", "")
        data.setdefault("dna_score", 50)
        return data
    except Exception as e:
        return {
            "archetype": "The Pragmatist", "archetype_desc": f"Could not parse DNA. Error: {e}",
            "archetype_icon": "🧬", "summary": "", "genes": [],
            "superpowers": [], "blind_spots": [], "compatibility_tags": [],
            "works_well_with": "", "clashes_with": "",
            "famous_developer_match": "", "dna_score": 50,
        }


def interview_ask(code: str, language: str, history: list, user_answer: str = "") -> dict:
    """
    Conducts a live technical interview about the code.
    Strictly evaluates whether the answer actually addresses the question asked.
    Scores are honest: irrelevant/wrong answers get 0-30, partial 30-60, good 60-80, excellent 80-100.
    history: list of {role, content} messages
    Returns: question, evaluation, answer_score, cumulative_score, stage, verdict
    """
    system = (
        f"You are a strict, honest senior {language} engineer conducting a FAANG-level technical interview. "
        "ABSOLUTE SCORING RULES you must follow without exception: "
        "1. If the candidate's answer does NOT address the question asked → answer_score: 0 to 20. "
        "2. If the candidate talks about something unrelated to the question → answer_score: 0 to 15. "
        "3. If the answer is vague with no technical substance → answer_score: 10 to 25. "
        "4. If the answer partially addresses the question with some correct points → answer_score: 30 to 55. "
        "5. If the answer correctly addresses the question with good reasoning → answer_score: 60 to 75. "
        "6. If the answer is thorough, technically accurate, and shows deep understanding → answer_score: 76 to 95. "
        "7. NEVER give above 40 for an answer that does not directly address the question asked. "
        "8. The evaluation must explicitly state whether the answer addressed the question or not. "
        "9. Questions must be specific to the actual code submitted — reference real variable/function names. "
        "Respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )

    history_text = ""
    if history:
        for msg in history:
            role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
            history_text += f"\n{role}: {msg['content']}"

    # Count only interviewer messages (questions asked so far)
    questions_asked = len([m for m in history if m["role"] == "assistant"])

    TOTAL_Q = 5

    if questions_asked == 0:
        # First question — no answer to evaluate yet
        user_prompt = f"""Start a technical interview. The candidate submitted this {language} code.

Read the code carefully. Ask your FIRST question.

QUESTION RULES:
- Must be about a SPECIFIC design decision, data structure choice, or logic in this exact code
- Reference the actual function name, variable name, or code pattern you are asking about
- Do NOT ask generic questions like "explain your code" — be specific
- Start at medium difficulty

Code submitted:
```{language}
{code}
```

Return ONLY this JSON:
{{
  "question": "Specific question referencing actual code element e.g. 'I see you used X in function Y — why did you choose this approach over Z?'",
  "question_context": "the specific code element this question is about e.g. function name, variable, pattern",
  "hint": "",
  "focus_area": "e.g. Data Structures / Algorithm Choice / Error Handling / Design Pattern",
  "difficulty": "medium",
  "stage": 1,
  "verdict": "in_progress",
  "answer_score": 0,
  "cumulative_score": 0,
  "evaluation": "",
  "final_feedback": "",
  "strengths": [],
  "improvements": []
}}"""

    elif questions_asked >= TOTAL_Q:
        # Final verdict — evaluate last answer and give overall verdict
        last_question = ""
        for m in reversed(history):
            if m["role"] == "assistant":
                last_question = m["content"]
                break

        user_prompt = f"""This is the FINAL question of the interview ({TOTAL_Q} of {TOTAL_Q}).

Code that was discussed:
```{language}
{code}
```

Full interview transcript:
{history_text}

The last question asked was: "{last_question}"
Candidate's final answer: "{user_answer}"

STEP 1 — Score this final answer strictly:
- Does it directly address the question "{last_question}"?
- If NO → answer_score 0-20
- If PARTIALLY → answer_score 25-55
- If YES with good reasoning → answer_score 60-80
- If YES with excellent depth → answer_score 81-95

STEP 2 — Compute final verdict:
- Review all the candidate's answers in the transcript
- Average score across all {TOTAL_Q} answers determines verdict:
  * 80-100 avg → strong_hire
  * 60-79 avg → hire
  * 35-59 avg → no_hire
  * 0-34 avg → strong_no_hire

Return ONLY this JSON:
{{
  "question": "",
  "question_context": "",
  "hint": "",
  "focus_area": "Final Assessment",
  "difficulty": "hard",
  "stage": {TOTAL_Q + 1},
  "verdict": "strong_hire|hire|no_hire|strong_no_hire",
  "answer_score": <integer 0-100 for THIS final answer>,
  "cumulative_score": <integer 0-100: honest overall average across all answers>,
  "evaluation": "2-3 sentences: did the final answer address the question? What was right/wrong?",
  "final_feedback": "4-5 sentences: honest overall assessment covering ALL answers in the interview, specific to this code",
  "strengths": ["specific strength observed in their answers, tied to actual code discussion"],
  "improvements": ["specific gap in their knowledge revealed by their answers"]
}}"""

    else:
        # Follow-up question — evaluate previous answer and ask next question
        last_question = ""
        for m in reversed(history):
            if m["role"] == "assistant":
                last_question = m["content"]
                break

        user_prompt = f"""Continue the technical interview. This is question {questions_asked + 1} of {TOTAL_Q}.

Code being discussed:
```{language}
{code}
```

Interview so far:
{history_text}

The previous question asked was: "{last_question}"
Candidate's answer to that question: "{user_answer}"

STEP 1 — Evaluate the answer STRICTLY:
First, ask yourself: "Did this answer actually address the question '{last_question}'?"
- If the candidate talked about something else entirely → answer_score: 0-20, evaluation must say "Your answer did not address the question"
- If the candidate gave a generic/vague response with no specifics → answer_score: 10-30
- If the candidate partially addressed it → answer_score: 30-55, evaluation points out what was missing
- If the candidate correctly addressed it → answer_score: 60-75
- If excellent with tradeoffs and depth → answer_score: 76-92

STEP 2 — Ask the next question:
- Must be about the ACTUAL CODE submitted
- Must reference a real function, variable, or pattern from the code
- Adjust difficulty based on their answer quality
- Do NOT repeat a topic already covered

Return ONLY this JSON:
{{
  "question": "Next specific question — must reference actual code element by name",
  "question_context": "the specific code element this question targets",
  "hint": "",
  "focus_area": "aspect being tested",
  "difficulty": "easy|medium|hard",
  "stage": {questions_asked + 1},
  "verdict": "in_progress",
  "answer_score": <integer 0-100 for the previous answer — be strict>,
  "cumulative_score": 0,
  "evaluation": "2-3 sentences: explicitly state whether the answer addressed the question, what was right, what was missing or wrong",
  "final_feedback": "",
  "strengths": [],
  "improvements": []
}}"""

    text = _call(system, user_prompt, temperature=0.2, max_tokens=1800)
    try:
        data = _extract_json(text)
        # Clamp scores
        data["answer_score"] = max(0, min(100, int(data.get("answer_score", 0))))
        data["cumulative_score"] = max(0, min(100, int(data.get("cumulative_score", 0))))
        data.setdefault("question", "Walk me through your design decisions for this code.")
        data.setdefault("question_context", "overall design")
        data.setdefault("hint", "")
        data.setdefault("focus_area", "Design")
        data.setdefault("difficulty", "medium")
        data.setdefault("stage", questions_asked + 1)
        data.setdefault("verdict", "in_progress")
        data.setdefault("evaluation", "")
        data.setdefault("final_feedback", "")
        if not isinstance(data.get("strengths"), list):
            data["strengths"] = []
        if not isinstance(data.get("improvements"), list):
            data["improvements"] = []
        return data
    except Exception as e:
        return {
            "question": "Can you explain the main design decision in this code?",
            "question_context": "overall design",
            "hint": "", "focus_area": "Design", "difficulty": "medium",
            "stage": questions_asked + 1, "verdict": "in_progress",
            "answer_score": 0, "cumulative_score": 0,
            "evaluation": f"Error parsing response: {e}",
            "final_feedback": "", "strengths": [], "improvements": [],
        }


def time_travel_code(code: str, language: str, era: str) -> dict:
    """
    Rewrites code as it would look in a specific era (past or future).
    era options: '1995', '2000', '2005', '2010', '2015', 'today', '2030', '2040'
    Returns: era_code, era_summary, changes, fun_facts, complexity_note
    """

    ERA_PROFILES = {
        "1995": {
            "label": "1995 — The Dawn Era",
            "icon": "🖥️",
            "desc": (
                "Rewrite this code as a developer in 1995 would write it. "
                "Use only ANSI C / early C++ / Perl / early Java style as appropriate. "
                "No modern OOP patterns, no generics, use raw arrays and manual memory. "
                "Add old-school comments like /* this function does X */. "
                "If Python, write as if it's Python 1.x — no list comprehensions, no f-strings, "
                "use % formatting, old-style classes (no 'object' inheritance). "
                "Favor procedural code. Use verbose variable names like 'szBuffer', 'lpData'."
            ),
            "fun_facts": [
                "Internet Explorer 1.0 launched this year 🌐",
                "Python 1.2 was the latest version — no list comprehensions yet",
                "Java was brand new — released May 1995",
                "Most code ran on 66MHz processors with 4MB RAM",
            ]
        },
        "2000": {
            "label": "2000 — Y2K Survivor",
            "icon": "💾",
            "desc": (
                "Rewrite this code as a developer in 2000 would write it. "
                "Use early Java/Python/PHP idioms. "
                "For Python: Python 2.0 style — use print as statement, xrange(), "
                "old-style string formatting with %, no type hints. "
                "Add Y2K-era defensive comments about date handling. "
                "Use verbose loops instead of comprehensions. "
                "OOP is allowed but keep classes simple."
            ),
            "fun_facts": [
                "Y2K bug fears dominated every code review 🐛",
                "Python 2.0 released October 2000",
                "PHP 4 was powering most of the web",
                "XML was the cool new data format — JSON didn't exist yet",
            ]
        },
        "2005": {
            "label": "2005 — Web 2.0 Era",
            "icon": "🌐",
            "desc": (
                "Rewrite this code as a developer in 2005 would write it. "
                "Python 2.4 style — use print statements, old string formatting, "
                "no f-strings, no walrus operator, no type hints. "
                "Use older patterns: manual sorting, old file I/O patterns. "
                "For JS: no ES6, use var, XMLHttpRequest instead of fetch, "
                "write jQuery-like verbose DOM manipulation. "
                "Ajax was the buzzword — add comments about it."
            ),
            "fun_facts": [
                "YouTube launched February 2005 📺",
                "jQuery didn't exist yet — raw DOM manipulation was the norm",
                "Python 2.4 was the latest stable release",
                "MySpace was the #1 social network",
            ]
        },
        "2010": {
            "label": "2010 — The Smartphone Era",
            "icon": "📱",
            "desc": (
                "Rewrite this code as a developer in 2010 would write it. "
                "Python 2.6/2.7 style — still print statements, but list comprehensions are ok. "
                "Use with statements for file I/O. No type hints. "
                "For JS: use jQuery patterns, callback functions for async (no Promises yet). "
                "Add comments mentioning REST APIs and mobile-first thinking."
            ),
            "fun_facts": [
                "iPhone 4 launched this year — mobile-first became a thing 📱",
                "Python 2.7 released July 2010 — the last Python 2 release",
                "Node.js was just 1 year old",
                "Bootstrap didn't exist yet — inline styles were common",
            ]
        },
        "2015": {
            "label": "2015 — The Modern Era Begins",
            "icon": "⚡",
            "desc": (
                "Rewrite this code as a developer in 2015 would write it. "
                "Python 3.4/3.5 style — f-strings not available yet (use .format()), "
                "asyncio is new and experimental, type hints just introduced in 3.5. "
                "For JS: ES6 was just released — use let/const, arrow functions, "
                "but Promises are new and async/await doesn't exist yet. "
                "React 0.13 was out — component-based thinking emerging."
            ),
            "fun_facts": [
                "ES6 (ES2015) revolutionized JavaScript with arrow functions and classes",
                "Python 3.5 introduced type hints and async/await",
                "Docker was only 2 years old — containers were exotic",
                "React.js was 2 years old and gaining traction",
            ]
        },
        "today": {
            "label": "2024 — Production Ready",
            "icon": "🚀",
            "desc": (
                "Rewrite this code to modern 2024 production standards. "
                "Python 3.12: use f-strings, type hints everywhere, dataclasses, "
                "pathlib, modern async patterns, match statements where applicable. "
                "JS: full ES2024, async/await, optional chaining, nullish coalescing. "
                "Best practices: error handling, logging, docstrings, single responsibility. "
                "This is the 'CodeRefine rewrite' — the best possible modern code."
            ),
            "fun_facts": [
                "Python 3.12 brings significant performance improvements 🐍",
                "TypeScript adoption hit all-time highs in 2024",
                "AI-assisted coding tools became mainstream this year",
                "Rust is the most loved language for the 9th year running",
            ]
        },
        "2030": {
            "label": "2030 — AI-Native (Speculative)",
            "icon": "🤖",
            "desc": (
                "SPECULATIVE: Rewrite this code as a developer in 2030 might write it. "
                "Imagine: Python 4.x with native AI annotations like @ai_verified, @self_optimizing. "
                "Use hypothetical syntax like 'infer' types, 'smart' data structures. "
                "Add comments assuming quantum-resistant hashing by default. "
                "Imagine async is implicit — everything is concurrent by default. "
                "Add fictional imports from imagined future libraries. "
                "Clearly mark the file header as SPECULATIVE/FICTIONAL."
            ),
            "fun_facts": [
                "⚠️ Speculative fiction — this era hasn't happened yet!",
                "Imagine: AI pair programmers are standard in every IDE",
                "Quantum-safe cryptography might be mandatory by law",
                "Edge computing could make server-side code rare",
            ]
        },
        "2040": {
            "label": "2040 — Post-AGI (Very Speculative)",
            "icon": "🌌",
            "desc": (
                "HIGHLY SPECULATIVE: Imagine code in 2040. "
                "Humans write intent, not instructions — use pseudocode-like 'intent declarations'. "
                "Invent a fictional 'NeuralLang' or 'IntentScript' syntax. "
                "Code might look like high-level goals with AI filling in details. "
                "Add comments like '# AI-compiled from intent v4.2'. "
                "Make it creative, funny, and clearly sci-fi. "
                "Mark everything as FICTIONAL/SPECULATIVE in the header."
            ),
            "fun_facts": [
                "⚠️ Highly speculative science fiction — for fun only!",
                "In this imagined future, developers write 'what' not 'how'",
                "Traditional debugging might be replaced by intent verification",
                "Moore's Law limits might be solved by biological computing",
            ]
        },
    }

    profile = ERA_PROFILES.get(era, ERA_PROFILES["today"])

    system = (
        "You are a programming historian and code archaeologist. "
        "You deeply understand how coding styles, idioms, and tools evolved across decades. "
        "Respond with a single valid JSON object only — no markdown, no prose outside JSON."
    )

    user = f"""Time-travel this {language} code to the era: {profile['label']}

ERA INSTRUCTIONS:
{profile['desc']}

Return ONLY this JSON:
{{
  "era_label": "{profile['label']}",
  "era_code": "COMPLETE rewritten {language} code in the style of this era — must be runnable or clearly labeled speculative",
  "era_summary": "2-3 sentences describing how and why the code changed for this era",
  "changes": [
    {{
      "what": "specific change made",
      "why": "why this was the norm in {era}",
      "modern_equivalent": "what we use today instead"
    }}
  ],
  "complexity_note": "How complexity/performance thinking differed in this era",
  "readability_score": <integer 0-100, how readable this era's code is by today's standards>,
  "nostalgia_factor": <integer 0-100, how nostalgic/retro this feels>
}}

Original {language} code:
```{language}
{code}
```"""

    text = _call(system, user, temperature=0.3, max_tokens=4096)
    try:
        data = _extract_json(text)
        data.setdefault("era_label", profile["label"])
        data.setdefault("era_code", code)
        data.setdefault("era_summary", "Time travel complete.")
        if not isinstance(data.get("changes"), list):
            data["changes"] = []
        data.setdefault("complexity_note", "")
        data.setdefault("readability_score", 50)
        data.setdefault("nostalgia_factor", 50)
        data["era_icon"] = profile["icon"]
        data["fun_facts"] = profile["fun_facts"]
        return data
    except Exception as e:
        return {
            "era_label": profile["label"],
            "era_icon": profile["icon"],
            "era_code": code,
            "era_summary": f"Could not parse time travel result. Error: {e}",
            "changes": [],
            "complexity_note": "",
            "readability_score": 50,
            "nostalgia_factor": 50,
            "fun_facts": profile["fun_facts"],
        }


def evaluate_challenge(user_code: str, challenge: dict, language: str) -> dict:
    """Evaluate a user's challenge solution."""
    system = (
        f"You are a senior {language} engineer evaluating coding submissions. "
        "Respond with a single valid JSON object only."
    )
    user = f"""Evaluate this {language} solution.

Challenge: {challenge.get('title', '')}
Problem: {challenge.get('description', '')}
Expected Complexity: {challenge.get('time_complexity', 'O(n)')}
Test Cases: {json.dumps(challenge.get('test_cases', [])[:3])}

User's solution:
```{language}
{user_code}
```

Return ONLY this JSON:
{{
  "passed": <true|false>,
  "score": <0-100>,
  "correctness": "correct|partially correct|incorrect",
  "time_complexity": "actual Big-O of this solution",
  "complexity_optimal": <true|false>,
  "feedback": "2-3 sentences of specific feedback referencing the user's actual code",
  "improvements": ["specific actionable improvement 1", "improvement 2"],
  "test_results": [
    {{"test": "input", "passed": true, "note": "brief"}}
  ]
}}"""

    text = _call(system, user, temperature=0.2, max_tokens=1024)
    try:
        data = _extract_json(text)
        data.setdefault("passed", False)
        data.setdefault("score", 0)
        data.setdefault("feedback", "Evaluation complete.")
        if not isinstance(data.get("improvements"), list):
            data["improvements"] = []
        if not isinstance(data.get("test_results"), list):
            data["test_results"] = []
        data.setdefault("correctness", "unknown")
        data.setdefault("time_complexity", "unknown")
        data.setdefault("complexity_optimal", False)
        return data
    except Exception as e:
        return {
            "passed": False, "score": 0,
            "feedback": f"Evaluation error: {e}. Raw: {text[:300]}",
            "improvements": [],
            "test_results": [], "correctness": "unknown",
            "time_complexity": "unknown", "complexity_optimal": False,
        }

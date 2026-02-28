# ⚡ CodeRefine
### Smarter Code. Cleaner Future.

> An AI-powered developer workspace that reviews, rewrites, explains, translates, and deeply analyzes your code — built with LLaMA 3.3 70B on Groq Cloud.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Code Review** | Deep AI analysis — real bugs with fixes, performance issues, security vulnerabilities, and best practices |
| ✍️ **Rewrite Code** | Production-quality AI rewrite with Big-O complexity comparison |
| 🌐 **Translate** | Idiomatic cross-language translation (Python → Go, JS → Rust, etc.) |
| 💡 **Explain** | Plain-English walkthrough of any code — purpose, inputs/outputs, edge cases |
| ⏳ **Code Time Traveler** | See your code rewritten across 8 eras — from 1995 to speculative 2040 |
| 🧬 **Code DNA** | Discover your developer archetype, superpowers, blind spots, and which famous developer you code like |
| 🎤 **Interview Simulator** | Live FAANG-style technical interview about your own code — strict per-answer scoring with hire/no-hire verdict |
| 💾 **Snippets** | Personal code snippet library with tags, search, and favorites |
| 🎯 **Challenges** | AI-generated coding challenges with hints, solutions, and auto-evaluation |
| 📊 **Analytics** | Track your code quality improvements over time |
| ⚙️ **Settings** | 5 themes × 5 accent colors — fully customizable workspace |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/coderefine.git
cd coderefine
pip install streamlit groq
```

### 2. Get a Groq API Key

Sign up free at [console.groq.com](https://console.groq.com) and create an API key.

### 3. Run

```bash
streamlit run app.py
```

App opens at **http://localhost:8501**

### 4. Enter your API key in the sidebar and start refining code ⚡

---

## 🏗️ Project Structure

```
coderefine/
├── app.py           # Main Streamlit app — all UI, navigation, pages (2,300+ lines)
├── ai_engine.py     # All AI functions — prompt engineering & Groq API calls (947 lines)
├── database.py      # SQLite database layer — auth, history, snippets, analytics (400 lines)
└── coderefine.db    # Auto-created SQLite database on first run
```

---

## 🤖 AI Stack

| Component | Choice | Why |
|---|---|---|
| **LLM** | LLaMA 3.3 70B Versatile | Best JSON accuracy, large context, strong code understanding |
| **Inference** | Groq Cloud (LPU) | 10–100x faster than GPU inference — near-instant responses |
| **Framework** | Streamlit | Pure Python, zero JavaScript, single command to run |
| **Database** | SQLite | Zero infrastructure — single file, bundled with Python |

---

## 🧬 Code DNA — How It Works

Code DNA analyzes your code for 7 objective traits and maps them to one of **8 developer archetypes**:

```
🏰 Defensive Architect   ⚡ Speed Demon      🔬 Perfectionist    🔧 Pragmatist
🎓 Academic              🤠 Cowboy           🪶 Minimalist       🏗️ Over-Engineer
```

Every gene score is evidence-based — pre-computed metrics (comment ratio, error handling presence, type annotations) are fed as ground-truth constraints to prevent AI inflation. The final DNA score is always recomputed as the mathematical average of all 7 genes.

---

## 🎤 Interview Simulator — Scoring Rules

The interviewer asks 5 questions specific to your actual code. Every answer is scored strictly:

| Score | Verdict | When |
|---|---|---|
| 0 – 20 | Irrelevant | Answer doesn't address the question |
| 21 – 35 | Vague | Generic, no technical substance |
| 36 – 55 | Partial | Some correct points, missing key aspects |
| 60 – 75 | Correct | Good reasoning, addresses the question |
| 76 – 95 | Excellent | Thorough, tradeoffs, alternatives |

Final verdict is computed as the honest average of all 5 scores — the AI cannot inflate it.

---

## ⏳ Code Time Traveler — 8 Eras

| Era | Style |
|---|---|
| 🖥️ **1995** | Procedural, manual memory, Python 1.x |
| 💾 **2000** | Y2K era, Python 2.0, early Java |
| 🌐 **2005** | Web 2.0, early AJAX, jQuery-like patterns |
| 📱 **2010** | Python 2.7, jQuery callbacks, mobile-first |
| ⚡ **2015** | ES6 just landed, Python 3.5, React emerging |
| 🚀 **2024** | Full production-ready modern code |
| 🤖 **2030** ⚠️ | Speculative AI-native patterns |
| 🌌 **2040** ⚠️ | Highly speculative intent-driven fiction |

---

## 🗄️ Database Schema

```sql
users               -- id, username, email, password_hash, theme, accent_color
reviews             -- user_id, language, original_code, review_json, rewritten_code,
                   --   bugs_count, perf_score, security_count, complexity, confidence,
                   --   orig_time_complexity, rw_time_complexity
snippets            -- user_id, title, description, language, code, tags, is_favorite
challenge_attempts  -- user_id, challenge_key, language, user_code, score, passed
```

Schema auto-migrates on startup — new columns are added safely without dropping data.

---

## 🔒 Security & Privacy

- **Passwords** — SHA-256 hashed, never stored in plaintext
- **API Keys** — Stored in browser session memory only, never persisted to disk or database
- **Code Storage** — Only first 800 chars of original code saved for analytics preview
- **SQL Injection** — All queries use parameterized placeholders via sqlite3
- **No Code Execution** — Code is analyzed as text only, never executed

---

## 📊 Analytics

The Analytics dashboard tracks your code quality over time:

- **Trend charts** — Performance score and complexity improvement across your last 15 reviews
- **Language breakdown** — Which languages you work in most
- **Complexity improvement** — Average Big-O score before vs. after AI rewrite
- **Review history** — Full table with all metrics per review

---

## 🎨 Theming

5 themes × 5 accent colors = 25 visual combinations, all saved per user account.

**Themes:** Dark · Midnight · Slate · Light · Warm  
**Accents:** Indigo · Cyan · Emerald · Rose · Amber

---

## 📦 Dependencies

```txt
streamlit
groq
```

That's it. No Docker, no separate backend, no build step.

---

## 🌐 Supported Languages

Python · JavaScript · TypeScript · Java · C++ · C · C# · Go · Rust · PHP · Ruby · Swift · Kotlin · Scala · R · MATLAB · Bash · SQL · HTML/CSS

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <b>Built for developers who care about code quality ⚡</b><br/>
  <i>Powered by LLaMA 3.3 70B · Groq Cloud · Streamlit</i>
</div>

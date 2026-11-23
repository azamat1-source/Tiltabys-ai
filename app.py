import json
import os
import re
import streamlit as st
from google import genai
from openai import OpenAI


# =========================
# БАПТАУЛАР
# =========================

MODEL = "gemini-3.8-flash"
QWEN_MODEL = "qwen3.7-plus"

st.set_page_config(
    page_title="Тілтабыс AI",
    page_icon="🎯",
    layout="centered"
)


# =========================
# ДИЗАЙН
# =========================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --green: #174c3c;
    --green-light: #e7f0e9;
    --cream: #f7f6ef;
    --text: #20352d;
    --muted: #718078;
}

.stApp {
    background: var(--cream);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 920px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--green) !important;
    font-weight: 800 !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 35px;
}

.brand-icon {
    background: var(--green);
    color: white;
    width: 42px;
    height: 42px;
    border-radius: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}

.brand-name {
    color: var(--green);
    font-weight: 800;
    font-size: 21px;
}

.hero {
    background: var(--green);
    color: white;
    border-radius: 24px;
    padding: 38px 34px;
    margin-bottom: 28px;
}

.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.14);
    color: #d9eadf;
    border-radius: 30px;
    padding: 7px 13px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 18px;
}

.hero h1 {
    color: white !important;
    font-size: 36px !important;
    line-height: 1.2;
    margin: 0 0 14px 0;
}

.hero p {
    color: #dce9e1;
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 0;
}

.info-card {
    background: white;
    border: 1px solid #e7e9e1;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;
    min-height: 112px;
}

.info-title {
    color: var(--green);
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 8px;
}

.info-text {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
}

div[data-testid="stForm"] {
    background: white;
    border: 1px solid #e7e9e1;
    border-radius: 20px;
    padding: 26px;
}

div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    border-radius: 11px;
}

.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button {
    background: var(--green);
    color: white;
    border: 1px solid var(--green);
    border-radius: 12px;
    padding: 12px 22px;
    font-weight: 700;
    min-height: 46px;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover {
    background: #23664f;
    color: white;
    border-color: #23664f;
}

div[data-testid="stChatMessage"] {
    background: white;
    border: 1px solid #e7e9e1;
    border-radius: 16px;
    padding: 14px;
}

div[data-testid="stProgressBar"] > div > div {
    background: var(--green);
}

.stAlert {
    border-radius: 13px;
}

.result-card {
    background: white;
    border: 1px solid #e7e9e1;
    border-radius: 18px;
    padding: 24px;
    margin: 15px 0;
}

.footer {
    text-align: center;
    color: #89958d;
    font-size: 12px;
    padding-top: 35px;
}

@media (max-width: 600px) {
    .hero {
        padding: 27px 22px;
    }

    .hero h1 {
        font-size: 28px !important;
    }

    div[data-testid="stForm"] {
        padding: 18px;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================
# AI PROMPT
# =========================

QUESTION_PROMPT = """
Сен тәжірибелі HR-менеджерсің.

Мамандық: {profession}
Деңгей: {level}

Сұрақтар базасы:
{questions}

Үміткерге арналған дәл 5 сұхбат сұрағын дайында.

Ережелер:
- Қазақ тілінде жаз.
- Мамандыққа сәйкес болсын.
- Тек берілген базадағы сұрақтарды пайдалан.
- Қайталанатын сұрақ болмасын.
- Жеңілден күрделіге қарай орналастыр.
- Тек JSON массивін қайтар.
- Markdown немесе түсініктеме қоспа.

Формат:
["1-сұрақ", "2-сұрақ", "3-сұрақ", "4-сұрақ", "5-сұрақ"]
"""


REPORT_PROMPT = """
Сен тәжірибелі HR-экспертсің.

Үміткердің сұхбат жауаптарын 100 балдық шкала бойынша бағала.

Мамандық: {profession}

Сұрақтар базасы мен бағалау критерийлері:
{questions}

Сұхбат:
{dialog}

БАҒАЛАУ ШКАЛАСЫ:
1. Мазмұн мен дұрыстығы: 40 балл
2. Құрылым мен логика: 20 балл
3. Нақтылық пен мысалдар: 20 балл
4. Коммуникация: 10 балл
5. Бейімделу: 10 балл

Ережелер:
- Әр жауапты criteria және good_answer арқылы салыстыр.
- Тек нақты жауаптарға сүйен.
- Бос немесе қате жауапқа төмен балл бер.
- Жалпы ұпай 100-ден аспасын.
- Қазақ тілінде жауап бер.

НӘТИЖЕ ФОРМАТЫ:

1. ЖАЛПЫ ҰПАЙ: X / 100

2. ДЕҢГЕЙ:
- 90–100: өте жақсы, жұмысқа дайын
- 75–89: жақсы, кішкене жетілдіру керек
- 60–74: орташа, негізгі олқылықтар бар
- 60-тан төмен: әлсіз, қайта дайындалу керек

3. КРИТЕРИЙЛЕР БОЙЫНША:
- Мазмұн: X / 40
- Құрылым: X / 20
- Нақтылық: X / 20
- Коммуникация: X / 10
- Бейімделу: X / 10

4. ЖІБЕРІЛГЕН ҚАТЕЛЕР

5. ЖАҚСАРТУҒА АРНАЛҒАН 3 КЕҢЕС
"""


# =========================
# ДЕРЕКТЕР БАЗАСЫ
# =========================

@st.cache_data
def load_db():
    with open("questions_db.json", encoding="utf-8") as f:
        data = json.load(f)

    return data["professions"]


# =========================
# GEMINI
# =========================

@st.cache_resource
def get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not key:
        return None

    return genai.Client(api_key=key)


def ask_gemini(prompt):
    try:
        client = get_client()

        if client is None:
            return None

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return response.text if response.text else None

    except Exception as e:
        st.warning(f"Gemini қатесі: {type(e).__name__}: {e}")
        return None


# =========================
# QWEN
# =========================

@st.cache_resource
def get_qwen_client():
    key = st.secrets.get("QWEN_API_KEY") or os.getenv("QWEN_API_KEY")

    if not key:
        return None

    return OpenAI(
        api_key=key,
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )


def ask_qwen(prompt):
    try:
        client = get_qwen_client()

        if client is None:
            return None

        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )

        return response.choices[0].message.content

    except Exception as e:
        st.warning(f"Qwen қатесі: {type(e).__name__}: {e}")
        return None


# =========================
# AI АУЫСТЫРУ
# =========================

def ask_ai(prompt):
    result = ask_gemini(prompt)

    if result:
        return result

    st.warning("Gemini қолжетімсіз. Qwen іске қосылып жатыр...")

    result = ask_qwen(prompt)

    if result:
        return result

    return None


def fill(prompt, **kw):
    for key, value in kw.items():
        prompt = prompt.replace(
            "{" + key + "}",
            str(value)
        )

    return prompt


# =========================
# SESSION STATE
# =========================

def init_state():
    defaults = {
        "stage": "form",
        "user": None,
        "profession": None,
        "questions": [],
        "answers": [],
        "question_index": 0,
        "questions_ready": False,
        "report": None
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset():
    for key in [
        "stage",
        "user",
        "profession",
        "questions",
        "answers",
        "question_index",
        "questions_ready",
        "report"
    ]:
        st.session_state.pop(key, None)

    init_state()


# =========================
# БАСТЫ БЕТ
# =========================

def step_form():
    db = load_db()

    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎯</div>
        <div class="brand-name">Тілтабыс AI</div>
    </div>

    <div class="hero">
        <div class="hero-tag">AI · HR INTERVIEW SIMULATOR</div>
        <h1>Мансабыңа сенімді қадам жаса.</h1>
        <p>
            Нақты жұмыс сұхбатына дайындал.
            Жасанды интеллект саған кәсіби сұрақтар қойып,
            жауаптарыңды бағалап, дамуыңа көмектеседі.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-title">01 · Сұхбат</div>
            <div class="info-text">
                Мамандыққа сәйкес 5 кәсіби сұрақ.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="info-title">02 · Бағалау</div>
            <div class="info-text">
                100 балдық жүйемен жауаптарды бағалау.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <div class="info-title">03 · Нәтиже</div>
            <div class="info-text">
                Қателер мен жақсартуға арналған кеңестер.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Сұхбатты бастау")
    st.caption("Өзің туралы ақпаратты толтыр.")

    with st.form("start"):
        name = st.text_input(
            "Атыңыз",
            placeholder="Атыңызды енгізіңіз"
        )

        professions = [
            p["profession"] for p in db
        ]

        prof = st.selectbox(
            "Мамандық / бағыт",
            professions
        )

        level = st.selectbox(
            "Деңгейіңіз",
            ["Бастаушы", "Орта", "Тәжірибелі"]
        )

        ok = st.form_submit_button(
            "Сұхбатты бастау →",
            use_container_width=True
        )

    if ok:
        if not name.strip():
            st.warning("Атыңызды енгізіңіз.")
            return

        prof_data = next(
            p for p in db
            if p["profession"] == prof
        )

        st.session_state.user = {
            "name": name.strip(),
            "level": level
        }

        st.session_state.profession = prof_data
        st.session_state.stage = "interview"
        st.session_state.questions = []
        st.session_state.answers = []
        st.session_state.question_index = 0
        st.session_state.questions_ready = False
        st.session_state.report = None

        st.rerun()

    st.markdown("""
    <div class="footer">
        Тілтабыс AI · Жасанды интеллект көмегімен кәсіби даму
    </div>
    """, unsafe_allow_html=True)


# =========================
# СҰХБАТ
# =========================

def step_interview():
    profession = st.session_state.profession["profession"]
    name = st.session_state.user["name"]

    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎯</div>
        <div class="brand-name">Тілтабыс AI</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"💬 {profession}")
    st.caption(f"Үміткер: {name}")

    if not st.session_state.questions_ready:
        st.info("Жасанды интеллект сұрақтар дайындап жатыр...")

        prompt = fill(
            QUESTION_PROMPT,
            profession=profession,
            level=st.session_state.user["level"],
            questions=json.dumps(
                st.session_state.profession["questions"],
                ensure_ascii=False
            )
        )

        with st.spinner("HR-менеджер дайындалуда..."):
            result = ask_ai(prompt)

        if result:
            try:
                start = result.find("[")
                end = result.rfind("]") + 1

                if start == -1 or end == 0:
                    raise ValueError("JSON массиві табылмады")

                questions = json.loads(result[start:end])

                if not isinstance(questions, list) or len(questions) != 5:
                    raise ValueError("Дәл 5 сұрақ алынбады")

                if not all(isinstance(q, str) for q in questions):
                    raise ValueError("Сұрақтардың форматы дұрыс емес")

                st.session_state.questions = questions
                st.session_state.questions_ready = True
                st.rerun()

            except Exception as e:
                st.warning(f"AI сұрақтарын оқу мүмкін болмады: {e}")

        fallback_questions = st.session_state.profession["questions"]
        questions = []

        for q in fallback_questions:
            if isinstance(q, dict):
                question = q.get("question")
                if question:
                    questions.append(question)
            elif isinstance(q, str):
                questions.append(q)

        if len(questions) < 5:
            st.error("Сұрақтар базасында кемінде 5 сұрақ болуы керек.")
            return

        st.session_state.questions = questions[:5]
        st.session_state.questions_ready = True

        st.warning("Дайын сұрақтар базасы қолданылды.")
        st.rerun()

    questions = st.session_state.questions
    answers = st.session_state.answers
    index = st.session_state.question_index

    st.progress(len(answers) / 5)
    st.caption(f"Сұрақ {min(index + 1, 5)} / 5")

    for i, answer in enumerate(answers):
        with st.chat_message("assistant"):
            st.write(f"**{i + 1}-сұрақ:** {questions[i]}")

        with st.chat_message("user"):
            st.write(answer)

    if index >= 5:
        st.success("Сұхбат аяқталды!")

        if st.button("📊 Нәтижені көру", type="primary"):
            st.session_state.stage = "report"
            st.rerun()

        return

    with st.chat_message("assistant"):
        st.write(questions[index])

    answer = st.chat_input("Жауабыңызды жазыңыз...")

    if answer and answer.strip():
        st.session_state.answers.append(answer.strip())
        st.session_state.question_index += 1
        st.rerun()


# =========================
# РЕЗЕРВТІК БАҒАЛАУ
# =========================

def fallback_report(questions, answers, db_questions):

    def words(text):
        return set(re.findall(
            r"[а-яәіңғүұқөһёa-z0-9]+",
            text.lower()
        ))

    stopwords = {
        "және", "мен", "бұл", "үшін", "туралы",
        "маған", "менің", "болады", "керек", "деп",
        "the", "and", "for", "with", "that"
    }

    reference_text = json.dumps(
        db_questions,
        ensure_ascii=False
    )

    reference_words = words(reference_text) - stopwords

    scores = {
        "Мазмұн": [],
        "Құрылым": [],
        "Нақтылық": [],
        "Коммуникация": [],
        "Бейімделу": []
    }

    errors = []

    for i, answer in enumerate(answers):
        text = answer.strip()
        tokens = words(text) - stopwords
        word_count = len(text.split())

        if not text or word_count < 3:
            errors.append(
                f"{i + 1}-жауап: жауап тым қысқа немесе толық емес."
            )

        overlap = len(tokens & reference_words)

        content = min(
            40,
            word_count * 0.35 + min(overlap, 10) * 1.2
        )

        sentences = len(re.findall(r"[.!?]+", text))

        structure = min(
            20,
            5 + sentences * 3 + (5 if word_count >= 25 else 0)
        )

        example_words = [
            "мысалы", "тәжірибе", "жоба", "нәтиже",
            "себебі", "өйткені", "өлшем", "есеп"
        ]

        examples = sum(
            1 for w in example_words
            if w in text.lower()
        )

        specificity = min(
            20,
            5 + examples * 3 +
            (5 if re.search(r"\d+", text) else 0)
        )

        communication = min(
            10,
            3 + min(word_count / 5, 7)
        )

        adaptive_words = [
            "үйрен", "бейім", "шешім", "қиындық",
            "дамыту", "тәжірибе", "жауапкершілік"
        ]

        adaptation = min(
            10,
            4 + sum(
                2 for w in adaptive_words
                if w in text.lower()
            )
        )

        if not text:
            content = structure = specificity = 0
            communication = adaptation = 0

        scores["Мазмұн"].append(content)
        scores["Құрылым"].append(structure)
        scores["Нақтылық"].append(specificity)
        scores["Коммуникация"].append(communication)
        scores["Бейімделу"].append(adaptation)

    final_scores = {
        key: round(sum(value) / len(value))
        if value else 0
        for key, value in scores.items()
    }

    total = sum(final_scores.values())

    if total >= 90:
        level = "Өте жақсы, жұмысқа дайын"
    elif total >= 75:
        level = "Жақсы, кішкене жетілдіру керек"
    elif total >= 60:
        level = "Орташа, негізгі олқылықтар бар"
    else:
        level = "Әлсіз, қайта дайындалу керек"

    if not errors:
        errors.append(
            "Қысқа жауаптар анықталған жоқ. "
            "Нақты кәсіби терминдер мен мысалдарды көбейтуге болады."
        )

    return f"""
# 📊 СҰХБАТ НӘТИЖЕСІ

**ЖАЛПЫ ҰПАЙ: {total} / 100**

**ДЕҢГЕЙ:** {level}

## Критерийлер бойынша

- Мазмұн: {final_scores['Мазмұн']} / 40
- Құрылым: {final_scores['Құрылым']} / 20
- Нақтылық: {final_scores['Нақтылық']} / 20
- Коммуникация: {final_scores['Коммуникация']} / 10
- Бейімделу: {final_scores['Бейімделу']} / 10

## Жіберілген қателер

{chr(10).join('- ' + e for e in errors)}

## Жақсартуға арналған 3 кеңес

1. Жауаптарыңызды нақты мысалдармен толықтырыңыз.
2. Кәсіби терминдерді дұрыс қолданып үйреніңіз.
3. Жауаптарыңызды жүйелі, логикалық ретпен жеткізіңіз.

---
*Ескерту: Бұл резервтік автоматты бағалау.
AI сараптамасы емес.*
"""


# =========================
# НӘТИЖЕ
# =========================

def step_report():
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎯</div>
        <div class="brand-name">Тілтабыс AI</div>
    </div>
    """, unsafe_allow_html=True)

    st.title("📊 Сұхбат нәтижесі")

    if st.session_state.report is None:
        questions = st.session_state.questions
        answers = st.session_state.answers

        dialog = ""

        for i in range(len(answers)):
            dialog += (
                f"\nСұрақ {i + 1}: {questions[i]}"
                f"\nҮміткердің жауабы: {answers[i]}\n"
            )

        prompt = fill(
            REPORT_PROMPT,
            profession=st.session_state.profession["profession"],
            questions=json.dumps(
                st.session_state.profession["questions"],
                ensure_ascii=False
            ),
            dialog=dialog
        )

        with st.spinner("AI жауаптарыңызды бағалап жатыр..."):
            report = ask_ai(prompt)

        if report is None:
            st.warning(
                "AI сервистері қолжетімсіз. "
                "Резервтік бағалау іске қосылды."
            )

            report = fallback_report(
                questions,
                answers,
                st.session_state.profession["questions"]
            )

        st.session_state.report = report

    st.success("Бағалау аяқталды!")

    st.markdown(
        f'<div class="result-card">{st.session_state.report}</div>',
        unsafe_allow_html=True
    )

    st.download_button(
        "⬇️ Есепті жүктеу (.txt)",
        data=st.session_state.report,
        file_name="interview_report.txt",
        mime="text/plain"
    )

    if st.button("🔄 Жаңадан бастау", use_container_width=True):
        reset()
        st.rerun()


# =========================
# ҚОСЫМШАНЫ ІСКЕ ҚОСУ
# =========================

init_state()

if st.session_state.stage == "form":
    step_form()

elif st.session_state.stage == "interview":
    step_interview()

elif st.session_state.stage == "report":
    step_report()

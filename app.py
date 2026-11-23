import json
import os
import re
import streamlit as st
from google import genai
from openai import OpenAI


# ==================================================
# 1. БАПТАУЛАР
# ==================================================

MODEL = "gemini-3.8-flash"
QWEN_MODEL = "qwen3.7-plus"

st.set_page_config(
    page_title="Тілтабыс AI",
    page_icon="🎯",
    layout="centered"
)


# ==================================================
# 2. ДИЗАЙН
# ==================================================

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


# ==================================================
# 3. ТІЛДЕР
# ==================================================

TEXT = {
    "Қазақша": {
        "name": "Атыңыз",
        "profession": "Мамандық / бағыт",
        "language": "Сұхбат тілі",
        "level": "Сұхбат деңгейі",
        "start": "Сұхбатты бастау →",
        "empty_name": "Атыңызды енгізіңіз.",
        "candidate": "Үміткер",
        "question": "Сұрақ",
        "answer_placeholder": "Жауабыңызды жазыңыз...",
        "finish": "Сұхбат аяқталды!",
        "result": "📊 Нәтижені көру",
        "new": "🔄 Жаңадан бастау",
        "base": "Базалық",
        "advanced": "Тереңдетілген",
        "preparing": "Жасанды интеллект сұрақтар дайындап жатыр...",
        "ai_ready": "HR-менеджер дайындалуда...",
        "fallback": "Дайын сұрақтар базасы қолданылды.",
        "no_questions": "Сұрақтар базасында кемінде 5 сұрақ болуы керек.",
        "report_loading": "AI жауаптарыңызды бағалап жатыр...",
        "report_done": "Бағалау аяқталды!",
        "report_error": "AI сервистері қолжетімсіз. Резервтік бағалау іске қосылды.",
        "download": "⬇️ Есепті жүктеу (.txt)",
        "title": "Мансабыңа сенімді қадам жаса.",
        "description": "Нақты жұмыс сұхбатына дайындал. Жасанды интеллект саған кәсіби сұрақтар қойып, жауаптарыңды бағалап, дамуыңа көмектеседі."
    },

    "Русский": {
        "name": "Ваше имя",
        "profession": "Профессия / направление",
        "language": "Язык собеседования",
        "level": "Уровень собеседования",
        "start": "Начать собеседование →",
        "empty_name": "Введите ваше имя.",
        "candidate": "Кандидат",
        "question": "Вопрос",
        "answer_placeholder": "Напишите ваш ответ...",
        "finish": "Собеседование завершено!",
        "result": "📊 Посмотреть результат",
        "new": "🔄 Начать заново",
        "base": "Базовый",
        "advanced": "Продвинутый",
        "preparing": "Искусственный интеллект готовит вопросы...",
        "ai_ready": "HR-менеджер готовится...",
        "fallback": "Используется резервная база вопросов.",
        "no_questions": "В базе должно быть не менее 5 вопросов.",
        "report_loading": "AI оценивает ваши ответы...",
        "report_done": "Оценивание завершено!",
        "report_error": "AI-сервисы недоступны. Запущена резервная оценка.",
        "download": "⬇️ Скачать отчет (.txt)",
        "title": "Сделайте уверенный шаг к карьере.",
        "description": "Подготовьтесь к настоящему собеседованию. Искусственный интеллект задаст профессиональные вопросы, оценит ваши ответы и поможет развиваться."
    }
}


# ==================================================
# 4. AI PROMPT
# ==================================================

QUESTION_PROMPT = """
Сен құрылыс саласындағы тәжірибелі HR-менеджерсің.

Мамандық: {profession}
Деңгей: {level}
Тіл: {language}

Сұрақтар базасы:
{questions}

Үміткерге дәл 5 кәсіби сұрақ дайында.

Ережелер:
- Барлық сұрақты көрсетілген тілде жаз.
- Базалық деңгейде негізгі кәсіби білімді тексер.
- Тереңдетілген деңгейде практикалық және ситуациялық сұрақтарды таңда.
- Берілген сұрақтар базасына сүйен.
- Мамандыққа қатысы жоқ сұрақ қоспа.
- Сұрақтарды жеңілден күрделіге қарай орналастыр.
- Қайталанатын сұрақ болмасын.
- Тек JSON массивін қайтар.
- Markdown немесе түсініктеме қоспа.

Формат:
["1-сұрақ", "2-сұрақ", "3-сұрақ", "4-сұрақ", "5-сұрақ"]
"""


FOLLOWUP_PROMPT = """
Сен құрылыс саласындағы тәжірибелі HR-мамансың.

Мамандық: {profession}
Деңгей: {level}
Тіл: {language}

Сұрақ: {question}

Үміткердің жауабы:
{answer}

Жауапты талда.

Егер жауап:
- тым қысқа болса;
- толық түсіндірілмесе;
- нақты мысалсыз болса;
- маңызды кәсіби тұсы ашылмаса,

бір нақтылаушы сұрақ дайында.

Егер жауап толық әрі нақты болса, қосымша сұрақ қажет емес.

Ережелер:
- Бір ғана қосымша сұрақ дайында.
- Мамандыққа тікелей қатысты болсын.
- Көрсетілген тілде жаз.
- Жауапта жоқ ақпаратты ойдан қоспа.

Тек JSON қайтар:

{"followup": "Қосымша сұрақ"}

Егер қосымша сұрақ қажет болмаса:

{"followup": null}
"""


REPORT_PROMPT = """
Сен құрылыс саласындағы тәжірибелі HR-экспертсің.

Мамандық: {profession}
Деңгей: {level}
Тіл: {language}

Сұрақтар базасы мен бағалау критерийлері:
{questions}

Сұхбат:
{dialog}

Үміткердің жауаптарын 100 балдық жүйемен бағала.

БАҒАЛАУ ШКАЛАСЫ:
1. Мазмұн мен кәсіби дұрыстығы: 40 балл
2. Құрылым мен логика: 20 балл
3. Нақтылық пен мысалдар: 20 балл
4. Коммуникация: 10 балл
5. Бейімделу және мәселені шешу: 10 балл

Ережелер:
- Әр жауапты сұрақтың критерийлерімен салыстыр.
- Жалпы ұпай 100-ден аспасын.
- Нақты қателерді көрсет.
- Жауапта жоқ ақпаратты үміткер айтты деп жазба.
- Қысқа жауапқа негізсіз жоғары балл берме.
- Құрылыс нормаларына қатысты нақты құжат пен тармақты
  тек сенімді білсең ғана көрсет.
- Нақты нормативтік дерек болмаса, оны тексеру қажеттігін айт.
- Нәтижені көрсетілген тілде жаз.

НӘТИЖЕ ФОРМАТЫ:

# СҰХБАТ НӘТИЖЕСІ

## 1. ЖАЛПЫ ҰПАЙ: X / 100

## 2. ДЕҢГЕЙ

90–100: өте жақсы
75–89: жақсы
60–74: орташа
0–59: төмен

## 3. КРИТЕРИЙЛЕР БОЙЫНША

- Мазмұн: X / 40
- Құрылым: X / 20
- Нақтылық: X / 20
- Коммуникация: X / 10
- Бейімделу: X / 10

## 4. ӘР ЖАУАПТЫҢ ТАЛДАУЫ

Әр сұрақ бойынша:
- Жауаптың артықшылықтары
- Кемшіліктері
- Ұсынылатын дұрыс бағыт

## 5. ЖІБЕРІЛГЕН ҚАТЕЛЕР

## 6. ЖАҚСАРТУҒА АРНАЛҒАН 3 КЕҢЕС
"""


# ==================================================
# 5. ДЕРЕКТЕР БАЗАСЫ
# ==================================================

@st.cache_data
def load_db():
    with open("questions_db.json", encoding="utf-8") as f:
        data = json.load(f)

    return data["professions"]


# ==================================================
# 6. GEMINI
# ==================================================

@st.cache_resource
def get_client():
    try:
        key = (
            st.secrets.get("GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

        if not key:
            return None

        return genai.Client(api_key=key)

    except Exception:
        return None


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
        print("Gemini error:", e)
        return None


# ==================================================
# 7. QWEN
# ==================================================

@st.cache_resource
def get_qwen_client():
    try:
        key = (
            st.secrets.get("QWEN_API_KEY")
            or os.getenv("QWEN_API_KEY")
        )

        if not key:
            return None

        return OpenAI(
            api_key=key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )

    except Exception:
        return None


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
        print("Qwen error:", e)
        return None


# ==================================================
# 8. AI АУЫСТЫРУ
# ==================================================

def ask_ai(prompt):
    result = ask_gemini(prompt)

    if result:
        return result

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


# ==================================================
# 9. JSON ОҚУ
# ==================================================

def extract_json(text):
    if not text:
        return None

    text = text.strip()

    # Markdown белгілерін алып тастау
    text = re.sub(r"```json|```", "", text).strip()

    # JSON массивін немесе объектісін табу
    start_obj = text.find("{")
    start_arr = text.find("[")

    starts = [
        x for x in [start_obj, start_arr]
        if x >= 0
    ]

    if not starts:
        return None

    start = min(starts)

    if text[start] == "[":
        end = text.rfind("]") + 1
    else:
        end = text.rfind("}") + 1

    if end <= start:
        return None

    try:
        return json.loads(text[start:end])
    except Exception:
        return None


# ==================================================
# 10. SESSION STATE
# ==================================================

def init_state():
    defaults = {
        "stage": "form",
        "user": None,
        "profession": None,
        "questions": [],
        "question_types": [],
        "answers": [],
        "question_index": 0,
        "questions_ready": False,
        "report": None,
        "language": "Қазақша",
        "level": "Базалық",
        "followup_count": 0
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset():
    keys = [
        "stage",
        "user",
        "profession",
        "questions",
        "question_types",
        "answers",
        "question_index",
        "questions_ready",
        "report",
        "language",
        "level",
        "followup_count"
    ]

    for key in keys:
        st.session_state.pop(key, None)

    init_state()


# ==================================================
# 11. БРЕНД
# ==================================================

def show_brand():
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🎯</div>
        <div class="brand-name">Тілтабыс AI</div>
    </div>
    """, unsafe_allow_html=True)


# ==================================================
# 12. БАСТЫ БЕТ
# ==================================================

def step_form():
    db = load_db()

    language = st.session_state.get("language", "Қазақша")
    t = TEXT[language]

    st.markdown(f"""
    <div class="brand">
        <div class="brand-icon">🎯</div>
        <div class="brand-name">Тілтабыс AI</div>
    </div>

    <div class="hero">
        <div class="hero-tag">AI · HR INTERVIEW SIMULATOR</div>
        <h1>{t["title"]}</h1>
        <p>{t["description"]}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-title">01 · Сұхбат</div>
            <div class="info-text">
                Мамандыққа сәйкес кәсіби сұрақтар.
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
            t["name"],
            placeholder="..."
        )

        professions = [
            p["profession"] for p in db
        ]

        prof = st.selectbox(
            t["profession"],
            professions
        )

        language = st.selectbox(
            t["language"],
            ["Қазақша", "Русский"]
        )

        if language == "Қазақша":
            levels = ["Базалық", "Тереңдетілген"]
        else:
            levels = ["Базовый", "Продвинутый"]

        level = st.selectbox(
            t["level"],
            levels
        )

        ok = st.form_submit_button(
            t["start"],
            use_container_width=True
        )

    if ok:
        if not name.strip():
            st.warning(t["empty_name"])
            return

        prof_data = next(
            p for p in db
            if p["profession"] == prof
        )

        st.session_state.user = {
            "name": name.strip()
        }

        st.session_state.profession = prof_data
        st.session_state.language = language

        if language == "Русский":
            st.session_state.level = (
                "Базалық"
                if level == "Базовый"
                else "Тереңдетілген"
            )
        else:
            st.session_state.level = level

        st.session_state.stage = "interview"
        st.session_state.questions = []
        st.session_state.question_types = []
        st.session_state.answers = []
        st.session_state.question_index = 0
        st.session_state.questions_ready = False
        st.session_state.report = None
        st.session_state.followup_count = 0

        st.rerun()

    st.markdown("""
    <div class="footer">
        Тілтабыс AI · Жасанды интеллект көмегімен кәсіби даму
    </div>
    """, unsafe_allow_html=True)


# ==================================================
# 13. СҰРАҚТАРДЫ ДАЙЫНДАУ
# ==================================================

def prepare_questions():
    profession = st.session_state.profession["profession"]
    language = st.session_state.language
    level = st.session_state.level

    db_questions = st.session_state.profession["questions"]

    prompt = fill(
        QUESTION_PROMPT,
        profession=profession,
        language=language,
        level=level,
        questions=json.dumps(
            db_questions,
            ensure_ascii=False
        )
    )

    with st.spinner(
        TEXT[language]["preparing"]
    ):
        result = ask_ai(prompt)

    questions = extract_json(result)

    if (
        isinstance(questions, list)
        and len(questions) == 5
        and all(
            isinstance(q, str) and q.strip()
            for q in questions
        )
    ):
        st.session_state.questions = questions
        st.session_state.question_types = [
            "main"
        ] * 5

    else:
        # AI жұмыс істемесе, резервтік база
        questions = []

        for q in db_questions:
            if isinstance(q, dict):
                question = q.get("question")
                if question:
                    questions.append(question)

            elif isinstance(q, str):
                questions.append(q)

        if len(questions) < 5:
            st.error(
                TEXT[language]["no_questions"]
            )
            return False

        st.session_state.questions = questions[:5]
        st.session_state.question_types = [
            "main"
        ] * 5

        if language == "Русский":
            # Резервтік сұрақтарды аударуға тырысу
            translate_prompt = f"""
            Переведи следующие профессиональные вопросы
            на русский язык. Сохрани их смысл.

            Верни только JSON-массив из 5 строк.

            {json.dumps(questions[:5], ensure_ascii=False)}
            """

            translated = extract_json(
                ask_ai(translate_prompt)
            )

            if (
                isinstance(translated, list)
                and len(translated) == 5
                and all(isinstance(q, str) for q in translated)
            ):
                st.session_state.questions = translated

        st.warning(
            TEXT[language]["fallback"]
        )

    st.session_state.questions_ready = True
    return True


# ==================================================
# 14. ҚОСЫМША СҰРАҚ
# ==================================================

def generate_followup(question, answer):
    profession = st.session_state.profession["profession"]
    language = st.session_state.language
    level = st.session_state.level

    prompt = fill(
        FOLLOWUP_PROMPT,
        profession=profession,
        language=language,
        level=level,
        question=question,
        answer=answer
    )

    result = ask_ai(prompt)
    data = extract_json(result)

    if not isinstance(data, dict):
        return None

    followup = data.get("followup")

    if (
        isinstance(followup, str)
        and followup.strip()
    ):
        return followup.strip()

    return None


# ==================================================
# 15. СҰХБАТ
# ==================================================

def step_interview():
    language = st.session_state.language
    t = TEXT[language]

    profession = st.session_state.profession["profession"]
    name = st.session_state.user["name"]

    show_brand()

    st.subheader(f"💬 {profession}")
    st.caption(f"{t['candidate']}: {name}")

    if not st.session_state.questions_ready:
        if not prepare_questions():
            return

        st.rerun()

    questions = st.session_state.questions
    answers = st.session_state.answers
    index = st.session_state.question_index

    total = len(questions)

    st.progress(
        min(len(answers) / max(total, 1), 1.0)
    )

    if index < total:
        st.caption(
            f"{t['question']} {index + 1} / {total}"
        )
    else:
        st.caption(
            f"{len(answers)} / {total}"
        )

    # Бұрынғы сұрақтар мен жауаптар
    for i, answer in enumerate(answers):
        if i >= len(questions):
            break

        with st.chat_message("assistant"):
            if st.session_state.question_types[i] == "followup":
                st.caption("Қосымша сұрақ")
            st.write(questions[i])

        with st.chat_message("user"):
            st.write(answer)

    # Сұхбат аяқталса
    if index >= total:
        st.success(t["finish"])

        if st.button(
            t["result"],
            type="primary",
            use_container_width=True
        ):
            st.session_state.stage = "report"
            st.rerun()

        return

    current_question = questions[index]
    current_type = st.session_state.question_types[index]

    with st.chat_message("assistant"):
        if current_type == "followup":
            st.caption("Қосымша сұрақ")
        st.write(current_question)

    answer = st.chat_input(
        t["answer_placeholder"]
    )

    if answer and answer.strip():
        answer = answer.strip()

        st.session_state.answers.append(answer)

        # Тереңдетілген деңгейде қосымша сұрақ
        is_advanced = (
            st.session_state.level == "Тереңдетілген"
        )

        is_main_question = (
            current_type == "main"
        )

        can_add_followup = (
            is_advanced
            and is_main_question
            and st.session_state.followup_count < 2
        )

        if can_add_followup:
            with st.spinner("Жауабыңыз талданып жатыр..."):
                followup = generate_followup(
                    current_question,
                    answer
                )

            if followup:
                insert_position = index + 1

                st.session_state.questions.insert(
                    insert_position,
                    followup
                )

                st.session_state.question_types.insert(
                    insert_position,
                    "followup"
                )

                st.session_state.followup_count += 1

        st.session_state.question_index += 1
        st.rerun()


# ==================================================
# 16. РЕЗЕРВТІК БАҒАЛАУ
# ==================================================

def fallback_report(questions, answers, db_questions):
    language = st.session_state.language

    def words(text):
        return set(re.findall(
            r"[а-яәіңғүұқөһёa-z0-9]+",
            text.lower()
        ))

    stopwords = {
        "және", "мен", "бұл", "үшін", "туралы",
        "маған", "менің", "болады", "керек", "деп",
        "the", "and", "for", "with", "that",
        "и", "в", "на", "для", "это", "что"
    }

    reference_text = json.dumps(
        db_questions,
        ensure_ascii=False
    )

    reference_words = words(reference_text) - stopwords

    scores = {
        "content": [],
        "structure": [],
        "specificity": [],
        "communication": [],
        "adaptation": []
    }

    errors = []

    for i, answer in enumerate(answers):
        text = answer.strip()
        tokens = words(text) - stopwords
        word_count = len(text.split())

        if not text or word_count < 3:
            errors.append(i + 1)

        overlap = len(tokens & reference_words)

        content = min(
            40,
            word_count * 0.35 + min(overlap, 10) * 1.2
        )

        sentences = len(re.findall(r"[.!?]+", text))

        structure = min(
            20,
            5 + sentences * 3 + (
                5 if word_count >= 25 else 0
            )
        )

        example_words = [
            "мысалы", "тәжірибе", "жоба", "нәтиже",
            "себебі", "өлшем", "есеп",
            "например", "опыт", "проект", "результат"
        ]

        examples = sum(
            1 for w in example_words
            if w in text.lower()
        )

        specificity = min(
            20,
            5 + examples * 3 + (
                5 if re.search(r"\d+", text) else 0
            )
        )

        communication = min(
            10,
            3 + min(word_count / 5, 7)
        )

        adaptive_words = [
            "үйрен", "бейім", "шешім", "қиындық",
            "дамыту", "тәжірибе", "жауапкершілік",
            "решение", "развитие", "ответственность"
        ]

        adaptation = min(
            10,
            4 + sum(
                2 for w in adaptive_words
                if w in text.lower()
            )
        )

        if not text:
            content = 0
            structure = 0
            specificity = 0
            communication = 0
            adaptation = 0

        scores["content"].append(content)
        scores["structure"].append(structure)
        scores["specificity"].append(specificity)
        scores["communication"].append(communication)
        scores["adaptation"].append(adaptation)

    final_scores = {
        key: round(sum(value) / len(value))
        if value else 0
        for key, value in scores.items()
    }

    total = min(100, sum(final_scores.values()))

    if language == "Қазақша":
        if total >= 90:
            level = "Өте жақсы"
        elif total >= 75:
            level = "Жақсы"
        elif total >= 60:
            level = "Орташа"
        else:
            level = "Төмен"

        error_text = (
            "\n".join(
                f"- {i}-жауап: жауап тым қысқа немесе толық емес."
                for i in errors
            )
            if errors else
            "- Қысқа жауаптар анықталған жоқ."
        )

        return f"""
# 📊 СҰХБАТ НӘТИЖЕСІ

**ЕСКЕРТУ: Бұл резервтік автоматты бағалау. AI сараптамасы емес.**

## 1. ЖАЛПЫ ҰПАЙ: {total} / 100

## 2. ДЕҢГЕЙ: {level}

## 3. КРИТЕРИЙЛЕР БОЙЫНША

- Мазмұн: {final_scores['content']} / 40
- Құрылым: {final_scores['structure']} / 20
- Нақтылық: {final_scores['specificity']} / 20
- Коммуникация: {final_scores['communication']} / 10
- Бейімделу: {final_scores['adaptation']} / 10

## 4. ЖІБЕРІЛГЕН ҚАТЕЛЕР

{error_text}

## 5. ЖАҚСАРТУҒА АРНАЛҒАН 3 КЕҢЕС

1. Жауаптарыңызды нақты мысалдармен толықтырыңыз.
2. Кәсіби терминдерді дұрыс қолданып үйреніңіз.
3. Жауаптарыңызды жүйелі, логикалық ретпен жеткізіңіз.
"""

    else:
        if total >= 90:
            level = "Отлично"
        elif total >= 75:
            level = "Хорошо"
        elif total >= 60:
            level = "Средний уровень"
        else:
            level = "Низкий уровень"

        error_text = (
            "\n".join(
                f"- Ответ {i}: слишком короткий или неполный."
                for i in errors
            )
            if errors else
            "- Критически коротких ответов не обнаружено."
        )

        return f"""
# 📊 РЕЗУЛЬТАТ СОБЕСЕДОВАНИЯ

**ВНИМАНИЕ: Это резервная автоматическая оценка, а не оценка AI-эксперта.**

## 1. ОБЩИЙ БАЛЛ: {total} / 100

## 2. УРОВЕНЬ: {level}

## 3. ОЦЕНКА ПО КРИТЕРИЯМ

- Содержание: {final_scores['content']} / 40
- Структура: {final_scores['structure']} / 20
- Конкретность: {final_scores['specificity']} / 20
- Коммуникация: {final_scores['communication']} / 10
- Адаптация: {final_scores['adaptation']} / 10

## 4. ДОПУЩЕННЫЕ ОШИБКИ

{error_text}

## 5. ТРИ СОВЕТА ПО УЛУЧШЕНИЮ

1. Дополняйте ответы конкретными примерами.
2. Изучайте профессиональные термины.
3. Излагайте мысли последовательно и логично.
"""


# ==================================================
# 17. НӘТИЖЕ
# ==================================================

def step_report():
    language = st.session_state.language
    t = TEXT[language]

    show_brand()

    st.title("📊 " + (
        "Сұхбат нәтижесі"
        if language == "Қазақша"
        else "Результат собеседования"
    ))

    if st.session_state.report is None:
        questions = st.session_state.questions
        answers = st.session_state.answers

        dialog = ""

        for i, answer in enumerate(answers):
            dialog += (
                f"\nСұрақ {i + 1}: {questions[i]}"
                f"\nҮміткердің жауабы: {answer}\n"
            )

        prompt = fill(
            REPORT_PROMPT,
            profession=st.session_state.profession["profession"],
            level=st.session_state.level,
            language=language,
            questions=json.dumps(
                st.session_state.profession["questions"],
                ensure_ascii=False
            ),
            dialog=dialog
        )

        with st.spinner(t["report_loading"]):
            report = ask_ai(prompt)

        if report is None:
            st.warning(t["report_error"])

            report = fallback_report(
                questions,
                answers,
                st.session_state.profession["questions"]
            )

        st.session_state.report = report

    st.success(t["report_done"])

    st.markdown(
        '<div class="result-card">',
        unsafe_allow_html=True
    )

    st.markdown(st.session_state.report)

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    st.download_button(
        t["download"],
        data=st.session_state.report,
        file_name="interview_report.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.button(
        t["new"],
        use_container_width=True
    ):
        reset()
        st.rerun()


# ==================================================
# 18. ҚОСЫМШАНЫ ІСКЕ ҚОСУ
# ==================================================

init_state()

if st.session_state.stage == "form":
    step_form()

elif st.session_state.stage == "interview":
    step_interview()

elif st.session_state.stage == "report":
    step_report()

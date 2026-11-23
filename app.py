import json
import os
import re
import streamlit as st
from google import genai
from openai import OpenAI


# =====================================================
# 1. БЕТ БАПТАУЛАРЫ
# =====================================================

st.set_page_config(
    page_title="Тілтабыс AI",
    page_icon="🏗️",
    layout="wide"
)

MODEL = "gemini-3.8-flash"
QWEN_MODEL = "qwen3.7-plus"

QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


# =====================================================
# 2. API КЛИЕНТТЕРІ
# =====================================================

@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_qwen_client():
    api_key = st.secrets.get("QWEN_API_KEY", "")
    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url=QWEN_BASE_URL
    )


def ask_ai(prompt):
    """
    Алдымен Gemini-ді қолданады.
    Gemini істемесе, Qwen-ге ауысады.
    """

    errors = []

    # Gemini
    try:
        client = get_gemini_client()

        if client:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            if response and response.text:
                return response.text

    except Exception as e:
        errors.append(f"Gemini: {str(e)}")

    # Qwen
    try:
        client = get_qwen_client()

        if client:
            response = client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5
            )

            result = response.choices[0].message.content

            if result:
                return result

    except Exception as e:
        errors.append(f"Qwen: {str(e)}")

    st.session_state.ai_errors = errors
    return None


# =====================================================
# 3. ДЕРЕКТЕР БАЗАСЫ
# =====================================================

def load_db():
    possible_paths = [
        "questions_db.json",
        "data/questions_db.json"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                if isinstance(data, dict):
                    return data.get("professions", [])

                return data

            except Exception as e:
                st.error(f"JSON файлын оқу қатесі: {e}")
                return []

    st.error("questions_db.json файлы табылмады.")
    return []


# =====================================================
# 4. МӘТІНДІ ӨҢДЕУ
# =====================================================

def extract_json(text):
    if not text:
        return None

    text = text.strip()

    # Markdown белгілерін алып тастау
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    # JSON массивін іздеу
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    # JSON объектісін іздеу
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            pass

    return None


def fill(prompt, **kwargs):
    for key, value in kwargs.items():
        prompt = prompt.replace("{" + key + "}", str(value))
    return prompt


def is_correct_language(text, language):
    """
    Орысша мәтінде қазақ тіліне тән әріптер болмауын тексереді.
    """

    if language == "Русский":
        kazakh_letters = r"[әіңғүұқөһӘІҢҒҮҰҚӨҺ]"
        return not bool(re.search(kazakh_letters, text))

    return True


# =====================================================
# 5. ИНТЕРФЕЙС МӘТІНДЕРІ
# =====================================================

TEXT = {
    "Қазақша": {
        "title": "Тілтабыс AI",
        "subtitle": "Құрылыс саласындағы кәсіби біліміңді тексер",
        "start": "Сұхбатты бастау",
        "name": "Атыңыз",
        "profession": "Мамандықты таңдаңыз",
        "level": "Сұхбат деңгейі",
        "basic": "Базалық",
        "advanced": "Тереңдетілген",
        "preparing": "Сұрақтар дайындалуда...",
        "no_questions": "Сұрақтарды дайындау мүмкін болмады.",
        "fallback": "AI сұрақтары қолжетімсіз. Деректер базасындағы сұрақтар қолданылды.",
        "question": "Сұрақ",
        "answer": "Жауабыңызды жазыңыз",
        "send": "Жауапты жіберу",
        "finish": "Сұхбатты аяқтау",
        "report": "Нәтиже",
        "score": "Жалпы нәтиже",
        "restart": "Қайта бастау",
        "download": "Есепті жүктеу",
        "your_answer": "Сіздің жауабыңыз",
        "ai_question": "AI сұхбат алушы",
        "progress": "Сұхбат барысы",
        "language": "Сұхбат тілі",
        "welcome": "Қош келдіңіз!",
        "name_required": "Атыңызды енгізіңіз.",
        "choose_profession": "Мамандықты таңдаңыз.",
        "next": "Келесі",
        "analysis": "Жауаптарыңыз талдануда...",
        "recommendations": "Ұсыныстар",
        "restart_info": "Жаңа сұхбат бастау үшін төмендегі батырманы басыңыз."
    },

    "Русский": {
        "title": "Тілтабыс AI",
        "subtitle": "Проверьте свои профессиональные знания в строительной сфере",
        "start": "Начать собеседование",
        "name": "Ваше имя",
        "profession": "Выберите профессию",
        "level": "Уровень собеседования",
        "basic": "Базовый",
        "advanced": "Продвинутый",
        "preparing": "Подготавливаем вопросы...",
        "no_questions": "Не удалось подготовить вопросы.",
        "fallback": "AI-вопросы недоступны. Использованы вопросы из базы данных.",
        "question": "Вопрос",
        "answer": "Введите ваш ответ",
        "send": "Отправить ответ",
        "finish": "Завершить собеседование",
        "report": "Результат",
        "score": "Общий результат",
        "restart": "Начать заново",
        "download": "Скачать отчет",
        "your_answer": "Ваш ответ",
        "ai_question": "AI-интервьюер",
        "progress": "Ход собеседования",
        "language": "Язык собеседования",
        "welcome": "Добро пожаловать!",
        "name_required": "Введите ваше имя.",
        "choose_profession": "Выберите профессию.",
        "next": "Далее",
        "analysis": "Анализируем ваши ответы...",
        "recommendations": "Рекомендации",
        "restart_info": "Нажмите кнопку ниже, чтобы начать новое собеседование."
    }
}


# =====================================================
# 6. AI СҰРАҚТАРЫН ДАЙЫНДАУ
# =====================================================

QUESTION_PROMPT = """
You are an experienced HR manager in the construction industry.

Profession: {profession}
Interview level: {level}
Required language: {language}

Question database:
{questions}

TASK:
Create exactly 5 professional interview questions.

STRICT LANGUAGE RULE:
- If the required language is Русский, ALL questions MUST be entirely in Russian.
- If the required language is Қазақша, ALL questions MUST be entirely in Kazakh.
- Never mix Kazakh and Russian.
- Translate the meaning of database questions into the required language.
- Do not copy Kazakh questions when Russian is requested.

OTHER RULES:
- Use the database as the basis.
- Basic level: test fundamental professional knowledge.
- Advanced level: use practical and situational questions.
- Arrange questions from easy to difficult.
- Avoid duplicates.

Return ONLY a valid JSON array of exactly 5 strings.
Do not add Markdown or explanations.
"""


def translate_questions(questions, language):
    if language == "Қазақша":
        return questions

    prompt = f"""
Translate these construction interview questions into Russian.

Every question must be entirely in Russian.
Do not use Kazakh words or Kazakh-specific letters.
Preserve the professional meaning.
Return only a JSON array containing exactly 5 strings.

Questions:
{json.dumps(questions, ensure_ascii=False)}
"""

    result = ask_ai(prompt)
    translated = extract_json(result)

    if (
        isinstance(translated, list)
        and len(translated) == len(questions)
        and all(
            isinstance(q, str)
            and q.strip()
            and is_correct_language(q, language)
            for q in translated
        )
    ):
        return translated

    return None


def get_fallback_questions(db_questions):
    questions = []

    for item in db_questions:
        if isinstance(item, dict):
            question = item.get("question")
            if question:
                questions.append(question)

        elif isinstance(item, str):
            questions.append(item)

    return questions[:5]


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

    with st.spinner(TEXT[language]["preparing"]):
        result = ask_ai(prompt)

    questions = extract_json(result)

    valid_questions = (
        isinstance(questions, list)
        and len(questions) == 5
        and all(
            isinstance(q, str)
            and q.strip()
            and is_correct_language(q, language)
            for q in questions
        )
    )

    if valid_questions:
        st.session_state.questions = questions
        st.session_state.question_types = ["main"] * 5
        st.session_state.questions_ready = True
        return True

    # AI сұрақтары дұрыс тілде болмаса, аударуға әрекет жасау
    if isinstance(questions, list) and len(questions) == 5:
        if all(isinstance(q, str) and q.strip() for q in questions):
            translated = translate_questions(questions, language)

            if translated:
                st.session_state.questions = translated
                st.session_state.question_types = ["main"] * 5
                st.session_state.questions_ready = True
                return True

    # Резервтік сұрақтар
    fallback = get_fallback_questions(db_questions)

    if len(fallback) < 5:
        st.error(TEXT[language]["no_questions"])
        return False

    if language == "Русский":
        fallback = translate_questions(fallback, language)

        if not fallback:
            st.error(
                "Не удалось подготовить вопросы на русском языке. "
                "Проверьте доступность AI-сервисов."
            )
            return False

    st.session_state.questions = fallback
    st.session_state.question_types = ["main"] * 5
    st.session_state.questions_ready = True

    st.warning(TEXT[language]["fallback"])
    return True


# =====================================================
# 7. ҚОСЫМША СҰРАҚТАР
# =====================================================

FOLLOWUP_PROMPT = """
You are an experienced construction industry HR interviewer.

Profession: {profession}
Interview language: {language}

Main question:
{question}

Candidate's answer:
{answer}

Create ONE short follow-up question.
It should clarify the candidate's answer or test practical understanding.

STRICT LANGUAGE RULE:
- If language is Русский, write entirely in Russian.
- If language is Қазақша, write entirely in Kazakh.
- Never mix languages.
- Do not use Kazakh-specific letters in Russian text.

Return only the question, without explanations.
"""


def generate_followup(question, answer):
    language = st.session_state.language

    prompt = fill(
        FOLLOWUP_PROMPT,
        profession=st.session_state.profession["profession"],
        language=language,
        question=question,
        answer=answer
    )

    result = ask_ai(prompt)

    if not result:
        return None

    result = result.strip().strip('"').strip("'")

    if not is_correct_language(result, language):
        translation_prompt = f"""
Translate this interview question into Russian.
Use only Russian. Do not use Kazakh-specific letters.
Return only the translated question.

Question:
{result}
"""
        translated = ask_ai(translation_prompt)

        if not translated:
            return None

        result = translated.strip().strip('"').strip("'")

        if not is_correct_language(result, language):
            return None

    return result


# =====================================================
# 8. НӘТИЖЕНІ БАҒАЛАУ
# =====================================================

REPORT_PROMPT = """
You are a professional HR expert in the construction industry.

Prepare an objective interview evaluation report.

Candidate: {name}
Profession: {profession}
Level: {level}
Language: {language}

Interview questions and answers:
{answers}

Evaluation criteria from the database:
{criteria}

SCORING:
- Professional knowledge: 40 points
- Practical thinking: 20 points
- Completeness of answers: 20 points
- Understanding of construction documentation and standards: 10 points
- Communication and clarity: 10 points

Total: 100 points.

IMPORTANT:
- Evaluate the actual answers, not assumed knowledge.
- Do not give full points for vague answers.
- Consider the profession and interview level.
- Explain strengths and weaknesses.
- Give specific recommendations for improvement.
- If the candidate did not answer a question, consider this in the score.

STRICT LANGUAGE RULE:
- If language is Русский, write the entire report in Russian.
- If language is Қазақша, write the entire report in Kazakh.
- Never mix languages.
- Do not use Kazakh-specific letters in Russian text.

REPORT STRUCTURE:
1. Overall score out of 100.
2. Professional knowledge assessment.
3. Strengths.
4. Weaknesses.
5. Recommendations.
6. Final HR conclusion.

Write a clear, professional and useful report.
"""


def build_answers_text():
    lines = []

    for i, item in enumerate(st.session_state.answers, start=1):
        lines.append(
            f"{i}. {item['question']}\n"
            f"Candidate answer: {item['answer']}"
        )

    return "\n\n".join(lines)


def fallback_report():
    """
    Бұл AI бағалауы емес.
    AI қызметтері істемеген жағдайда қолданылатын
    қарапайым резервтік бағалау.
    """

    language = st.session_state.language
    answers = st.session_state.answers

    total_words = sum(
        len(item["answer"].split())
        for item in answers
    )

    answered = sum(
        1 for item in answers
        if item["answer"].strip()
    )

    if answered == 0:
        score = 0
    else:
        completeness = answered / max(len(answers), 1)
        average_words = total_words / max(answered, 1)

        score = int(
            completeness * 50
            + min(average_words / 40, 1) * 50
        )

    score = min(score, 100)

    if language == "Русский":
        report = f"""
# Результат собеседования

**Кандидат:** {st.session_state.user}
**Профессия:** {st.session_state.profession["profession"]}
**Уровень:** {st.session_state.level}

## Общий результат: {score}/100

Ответов получено: {answered} из {len(answers)}.

Количество слов в ответах: {total_words}.

## Анализ

Оценка сформирована автоматически по количеству ответов и их объему.
Это резервная оценка, а не полноценная экспертная оценка AI.

## Рекомендации

- Изучайте профессиональную терминологию.
- Отвечайте конкретно и последовательно.
- Приводите практические примеры из строительной сферы.
- Повторите основные нормативные документы и строительные процессы.

## Заключение

Для более точной оценки необходимо пройти полноценный анализ ответов с помощью AI.
"""
    else:
        report = f"""
# Сұхбат нәтижесі

**Үміткер:** {st.session_state.user}
**Мамандық:** {st.session_state.profession["profession"]}
**Деңгей:** {st.session_state.level}

## Жалпы нәтиже: {score}/100

Жауап берілген сұрақтар: {answered}/{len(answers)}.

Жауаптардағы сөз саны: {total_words}.

## Талдау

Баға жауаптардың саны мен көлеміне қарай автоматты түрде есептелді.
Бұл толыққанды AI сараптамасы емес, резервтік бағалау болып табылады.

## Ұсыныстар

- Кәсіби терминдерді меңгеріңіз.
- Сұрақтарға нақты әрі жүйелі жауап беріңіз.
- Құрылыс саласынан практикалық мысалдар келтіріңіз.
- Негізгі нормативтік құжаттар мен құрылыс процестерін қайталаңыз.

## Қорытынды

Нақтырақ бағалау үшін жауаптарды AI арқылы толық талдау қажет.
"""

    return report, score


def generate_report():
    language = st.session_state.language

    answers_text = build_answers_text()

    criteria = json.dumps(
        st.session_state.profession["questions"],
        ensure_ascii=False,
        indent=2
    )

    prompt = fill(
        REPORT_PROMPT,
        name=st.session_state.user,
        profession=st.session_state.profession["profession"],
        level=st.session_state.level,
        language=language,
        answers=answers_text,
        criteria=criteria
    )

    with st.spinner(TEXT[language]["analysis"]):
        result = ask_ai(prompt)

    if result:
        result = result.strip()

        if is_correct_language(result, language):
            st.session_state.report = result
            st.session_state.report_is_ai = True
            return

        # Есеп басқа тілде келсе, аударуға әрекет жасау
        translation_prompt = f"""
Translate the following complete interview evaluation report into Russian.

Use professional Russian.
Do not use Kazakh words or Kazakh-specific letters.
Preserve all scores, headings, recommendations and meaning.
Return only the translated report.

Report:
{result}
"""
        translated = ask_ai(translation_prompt)

        if translated and is_correct_language(translated, language):
            st.session_state.report = translated.strip()
            st.session_state.report_is_ai = True
            return

    report, score = fallback_report()

    st.session_state.report = report
    st.session_state.report_is_ai = False
    st.session_state.fallback_score = score


# =====================================================
# 9. SESSION STATE
# =====================================================

DEFAULT_STATE = {
    "stage": "form",
    "user": "",
    "profession": None,
    "level": "Базалық",
    "language": "Қазақша",
    "questions": [],
    "question_types": [],
    "answers": [],
    "question_index": 0,
    "questions_ready": False,
    "report": None,
    "report_is_ai": False,
    "followup_count": 0,
    "ai_errors": []
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_app():
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value


# =====================================================
# 10. CSS ДИЗАЙН
# =====================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F5F7F2;
}

.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #173F35, #276B52);
    color: white;
    padding: 42px;
    border-radius: 22px;
    margin-bottom: 28px;
}

.hero h1 {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 10px;
}

.hero p {
    font-size: 17px;
    color: #E0EEE6;
}

.info-card {
    background: white;
    border: 1px solid #E5EAE4;
    border-radius: 16px;
    padding: 22px;
    min-height: 145px;
}

.info-card h3 {
    color: #214E3E;
    font-size: 19px;
}

.info-card p {
    color: #68766E;
    font-size: 14px;
}

.section-title {
    color: #214E3E;
    font-size: 25px;
    font-weight: 750;
    margin-bottom: 14px;
}

.question-card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #E5EAE4;
    margin: 12px 0 20px 0;
}

.stButton > button {
    background: #24634B;
    color: white;
    border: none;
    border-radius: 10px;
    min-height: 45px;
    font-weight: 600;
}

.stButton > button:hover {
    background: #194B38;
    color: white;
    border: none;
}

[data-testid="stProgressBar"] > div > div {
    background-color: #24634B;
}

.footer {
    text-align: center;
    color: #89938C;
    font-size: 13px;
    padding-top: 35px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 11. ЖОҒАРҒЫ БӨЛІМ
# =====================================================

language = st.session_state.language
t = TEXT[language]

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(
        f"""
        <div style="font-size:24px;font-weight:800;color:#214E3E;">
            🏗️ Тілтабыс AI
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    selected_language = st.selectbox(
        "Тіл / Язык",
        ["Қазақша", "Русский"],
        index=["Қазақша", "Русский"].index(language),
        key="language_selector"
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()


# =====================================================
# 12. БАСТЫ БЕТ
# =====================================================

if st.session_state.stage == "form":

    st.markdown(
        f"""
        <div class="hero">
            <h1>{t["title"]}</h1>
            <p>{t["subtitle"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-card">
            <h3>🎯 Кәсіби сұхбат</h3>
            <p>Құрылыс саласындағы мамандықтар бойынша сұрақтар.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <h3>🤖 AI бағалау</h3>
            <p>Жауаптарыңызды талдау және нәтижені бағалау.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-card">
            <h3>📊 Жеке есеп</h3>
            <p>Күшті және әлсіз тұстарыңызды анықтау.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<div class="section-title">{t["welcome"]}</div>',
        unsafe_allow_html=True
    )

    professions = load_db()

    if professions:
        profession_names = [
            item["profession"]
            for item in professions
        ]

        with st.form("interview_form"):

            name = st.text_input(t["name"])

            selected_profession = st.selectbox(
                t["profession"],
                profession_names
            )

            level_options = (
                ["Базалық", "Тереңдетілген"]
                if language == "Қазақша"
                else ["Базовый", "Продвинутый"]
            )

            selected_level = st.selectbox(
                t["level"],
                level_options
            )

            submitted = st.form_submit_button(
                t["start"],
                use_container_width=True
            )

            if submitted:

                if not name.strip():
                    st.error(t["name_required"])

                else:
                    profession_data = next(
                        item for item in professions
                        if item["profession"] == selected_profession
                    )

                    st.session_state.user = name.strip()
                    st.session_state.profession = profession_data

                    if selected_level in ["Базалық", "Базовый"]:
                        st.session_state.level = "Базалық"
                    else:
                        st.session_state.level = "Тереңдетілген"

                    st.session_state.answers = []
                    st.session_state.question_index = 0
                    st.session_state.followup_count = 0
                    st.session_state.questions_ready = False
                    st.session_state.report = None
                    st.session_state.report_is_ai = False
                    st.session_state.stage = "interview"

                    st.rerun()


# =====================================================
# 13. СҰХБАТ БӨЛІМІ
# =====================================================

elif st.session_state.stage == "interview":

    language = st.session_state.language
    t = TEXT[language]

    if not st.session_state.questions_ready:
        success = prepare_questions()

        if success:
            st.rerun()
        else:
            if st.button(t["restart"]):
                reset_app()
                st.rerun()
            st.stop()

    questions = st.session_state.questions
    index = st.session_state.question_index

    if index >= len(questions):
        st.session_state.stage = "report"
        st.rerun()

    st.markdown(
        f'<div class="section-title">{t["ai_question"]}</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"**{st.session_state.user}** · "
        f"{st.session_state.profession['profession']}"
    )

    progress = index / len(questions)

    st.progress(progress)

    st.caption(
        f"{t['progress']}: {index} / {len(questions)}"
    )

    current_question = questions[index]

    st.markdown(
        f"""
        <div class="question-card">
            <div style="color:#738078;font-size:14px;">
                {t["question"]} {index + 1}
            </div>
            <h3 style="color:#214E3E;margin-top:10px;">
                {current_question}
            </h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Бұрын жіберілген жауаптарды көрсету
    for i, item in enumerate(st.session_state.answers):
        with st.chat_message("assistant"):
            st.write(f"**{t['question']} {i + 1}:**")
            st.write(item["question"])

        with st.chat_message("user"):
            st.write(item["answer"])

    answer = st.chat_input(t["answer"])

    if answer and answer.strip():

        st.session_state.answers.append({
            "question": current_question,
            "answer": answer.strip(),
            "type": st.session_state.question_types[index]
        })

        # Тереңдетілген деңгейде 2 қосымша сұраққа дейін
        if (
            st.session_state.level == "Тереңдетілген"
            and st.session_state.followup_count < 2
            and st.session_state.question_types[index] == "main"
        ):

            followup = generate_followup(
                current_question,
                answer.strip()
            )

            if followup:
                st.session_state.questions.insert(
                    index + 1,
                    followup
                )

                st.session_state.question_types.insert(
                    index + 1,
                    "followup"
                )

                st.session_state.followup_count += 1

        st.session_state.question_index += 1

        if st.session_state.question_index >= len(
            st.session_state.questions
        ):
            st.session_state.stage = "report"

        st.rerun()

    st.markdown("---")

    if st.button(
        t["finish"],
        use_container_width=True
    ):
        if st.session_state.answers:
            st.session_state.stage = "report"
            st.rerun()
        else:
            st.warning(t["answer"])


# =====================================================
# 14. НӘТИЖЕ БӨЛІМІ
# =====================================================

elif st.session_state.stage == "report":

    language = st.session_state.language
    t = TEXT[language]

    if st.session_state.report is None:
        generate_report()

    st.markdown(
        f'<div class="section-title">{t["report"]}</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"**{st.session_state.user}** · "
        f"{st.session_state.profession['profession']}"
    )

    if st.session_state.report_is_ai:
        st.success(
            "AI талдауы дайын."
            if language == "Қазақша"
            else "AI-анализ готов."
        )
    else:
        st.warning(
            "Резервтік бағалау қолданылды. Бұл толық AI бағалауы емес."
            if language == "Қазақша"
            else "Использована резервная оценка. Это не полноценная оценка AI."
        )

    st.markdown("---")

    st.markdown(
        st.session_state.report
    )

    st.markdown("---")

    report_text = st.session_state.report

    st.download_button(
        label=t["download"],
        data=report_text.encode("utf-8"),
        file_name="tiltabys_ai_report.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.write(t["restart_info"])

    if st.button(
        t["restart"],
        use_container_width=True
    ):
        reset_app()
        st.rerun()


# =====================================================
# 15. FOOTER
# =====================================================

st.markdown("""
<div class="footer">
    Тілтабыс AI · Құрылыс саласындағы кәсіби сұхбат платформасы
</div>
""", unsafe_allow_html=True)

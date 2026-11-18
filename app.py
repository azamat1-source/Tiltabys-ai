import json
import os
import time
import re
import streamlit as st
from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"

QUESTION_PROMPT = """
Сен тәжірибелі HR-менеджерсің.

Мамандық: {profession}
Деңгей: {level}

Сұрақтар базасы:
{questions}

Осы мәліметтерге сүйеніп, үміткерге арналған дәл 5 сұхбат сұрағын дайында.

Ережелер:
- Сұрақтар қазақ тілінде болсын.
- Сұрақтар мамандыққа сәйкес болсын.
- Сұрақтарды тек берілген базадан ал.
- Сұрақтарды қайталама.
- Біртіндеп жеңілден күрделіге қарай орналастыр.
- Тек JSON массивін қайтар.
- Markdown немесе қосымша түсініктеме жазба.

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
- Әр жауапты базадағы criteria және good_answer-мен салыстыр.
- Тек үміткердің нақты жауаптарына сүйен.
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

st.set_page_config(
    page_title="Тілтабыс AI",
    page_icon="🎯",
    layout="centered"
)


@st.cache_data
def load_db():
    with open("questions_db.json", encoding="utf-8") as f:
        return json.load(f)["professions"]


@st.cache_resource
def get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        st.error("GEMINI_API_KEY табылмады.")
        st.stop()
    return genai.Client(api_key=key)


def ask_gemini(prompt):
    for attempt in range(3):
        try:
            response = get_client().models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.6
                )
            )
            return response.text or None

        except Exception as e:
            error_text = str(e)

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                return None

            elif "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt == 2:
                    return None

                time.sleep(5 * (attempt + 1))

           else:
              st.error(f"Gemini қатесі: {error_text}")
    return None


def fill(prompt, **kw):
    for key, value in kw.items():
        prompt = prompt.replace("{" + key + "}", str(value))
    return prompt


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
        "stage", "user", "profession",
        "questions", "answers", "question_index",
        "questions_ready", "report"
    ]:
        st.session_state.pop(key, None)


def step_form():
    st.title("🎯 Тілтабыс AI")
    st.caption(
        "ЖИ-HR сұхбат симуляторы: 5 сұрақ, "
        "100 балдық баға және жақсарту кеңестері"
    )

    db = load_db()

    with st.form("start"):
        name = st.text_input("Атыңыз")

        prof = st.selectbox(
            "Мамандық / бағыт",
            [p["profession"] for p in db]
        )

        level = st.selectbox(
            "Деңгейіңіз",
            ["Бастаушы", "Орта", "Тәжірибелі"]
        )

        ok = st.form_submit_button("Сұхбатты бастау")

    if ok:
        if not name.strip():
            st.warning("Атыңызды енгізіңіз.")
            return

        prof_data = next(
            p for p in db if p["profession"] == prof
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


def step_interview():
    st.subheader(
        f"💬 {st.session_state.profession['profession']} · "
        f"{st.session_state.user['name']}"
    )

    if not st.session_state.questions_ready:
        st.info("Жасанды интеллект сұхбат сұрақтарын дайындап жатыр...")

        prompt = fill(
            QUESTION_PROMPT,
            profession=st.session_state.profession["profession"],
            level=st.session_state.user["level"],
            questions=json.dumps(
                st.session_state.profession["questions"],
                ensure_ascii=False
            )
        )

        with st.spinner("HR-менеджер дайындалуда..."):
            result = ask_gemini(prompt)

        if not result:
            fallback_questions = (
                st.session_state.profession["questions"]
            )

            questions = []

            for q in fallback_questions:
                if isinstance(q, dict):
                    question = q.get("question")
                    if question:
                        questions.append(question)
                elif isinstance(q, str):
                    questions.append(q)

            if len(questions) < 5:
                st.error("Сұрақтар базасында 5 сұрақ жеткіліксіз.")
                return

            st.session_state.questions = questions[:5]
            st.session_state.questions_ready = True

            st.warning(
                "Gemini лимиті таусылды. "
                "Дайын сұрақтар базасы қолданылды."
            )
            st.rerun()

        try:
            start = result.find("[")
            end = result.rfind("]") + 1

            if start == -1 or end == 0:
                raise ValueError("JSON массиві табылмады")

            questions = json.loads(result[start:end])

            if not isinstance(questions, list) or len(questions) != 5:
                raise ValueError("5 сұрақ алынбады")

            st.session_state.questions = questions
            st.session_state.questions_ready = True
            st.rerun()

        except Exception as e:
            st.error(f"Сұрақтарды оқу мүмкін болмады: {e}")
            st.code(str(result))
            return

    questions = st.session_state.questions
    answers = st.session_state.answers
    index = st.session_state.question_index

    st.progress(len(answers) / 5)
    st.caption(f"Сұрақ {index + 1} / 5")

    for i, answer in enumerate(answers):
        with st.chat_message("assistant"):
            st.write(f"**{i + 1}-сұрақ:** {questions[i]}")

        with st.chat_message("user"):
            st.write(answer)

    if index >= 5:
        st.success("Сұхбат аяқталды! Рақмет.")
        if st.button("📊 Нәтижені көру", type="primary"):
            st.session_state.stage = "report"
            st.rerun()
        return

    with st.chat_message("assistant"):
        st.write(questions[index])

    answer = st.chat_input("Жауабыңызды жазыңыз...")

    if answer:
        st.session_state.answers.append(answer.strip())
        st.session_state.question_index += 1
        st.rerun()

def fallback_report(questions, answers, db_questions):
    """Gemini қолжетімсіз болғанда қарапайым бағалау."""

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
        db_questions, ensure_ascii=False
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

        # 1. Мазмұн: 40 балл
        overlap = len(tokens & reference_words)
        content = min(40, word_count * 0.35 +
                      min(overlap, 10) * 1.2)

        # 2. Құрылым: 20 балл
        sentences = len(re.findall(r"[.!?]+", text))
        structure = min(20, 5 + sentences * 3 +
                        (5 if word_count >= 25 else 0))

        # 3. Нақтылық: 20 балл
        example_words = [
            "мысалы", "тәжірибе", "жоба", "нәтиже",
            "себебі", "өйткені", "өлшем", "есеп"
        ]
        examples = sum(1 for w in example_words if w in text.lower())
        specificity = min(20, 5 + examples * 3 +
                          (5 if re.search(r"\d+", text) else 0))

        # 4. Коммуникация: 10 балл
        communication = min(10, 3 + min(word_count / 5, 7))

        # 5. Бейімделу: 10 балл
        adaptive_words = [
            "үйрен", "бейім", "шешім", "қиындық",
            "дамыту", "тәжірибе", "жауапкершілік"
        ]
        adaptation = min(
            10, 4 + sum(
                2 for w in adaptive_words if w in text.lower()
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
            "Дегенмен, нақты кәсіби терминдер мен мысалдарды көбейтуге болады."
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
AI сараптамасы емес. Баға жауаптың ұзындығы мен
қарапайым мәтіндік белгілеріне негізделген.*
"""


def step_report():
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

        with st.spinner("Жауаптарыңыз бағалануда..."):
            report = ask_gemini(prompt)

            if report is None:
                st.warning(
                    "Gemini API қолжетімсіз. "
                    "Резервтік бағалау жүйесі іске қосылды."
                )

                report = fallback_report(
                    questions,
                    answers,
                    st.session_state.profession["questions"]
                )

            st.session_state.report = report

    st.markdown(st.session_state.report)

    st.download_button(
        "⬇️ Есепті жүктеу (.txt)",
        st.session_state.report,
        file_name="interview_report.txt"
    )

    if st.button("🔄 Жаңадан бастау"):
        reset()
        st.rerun()

init_state()

if st.session_state.stage == "form":
    step_form()
elif st.session_state.stage == "interview":
    step_interview()
elif st.session_state.stage == "report":
    step_report()

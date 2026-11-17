import json
import os
import streamlit as st
from google import genai
from google.genai import types

MODEL = "gemini-3.8-flash"
MAX_USER_TURNS = 12  # қауіпсіздік шегі: сұхбат шексіз созылмасын
END_MARKER = "Сұхбат аяқталды"

INTERVIEW_PROMPT = """Сен тәжірибелі HR-менеджерсің және үміткермен жұмысқа орналасу сұхбатын жүргізіп жатырсың.

ДЕРЕКТЕР:
- Таңдалған мамандық: {profession}
- Сұрақтар базасы (questions_db.json): {questions}

ЕРЕЖЕЛЕР:
1. Сұхбатты қазақ тілінде, сыпайы және кәсіби тонда жүргіз.
2. Сұхбат басында қысқаша амандасып, мамандықты атап, сұхбат 5 сұрақтан тұратынын айт.
3. Дәл 5 негізгі сұрақ қой. Сұрақтарды тек базадан таңда, базада жоқ сұрақ ойлап таппа.
4. Бір уақытта тек бір сұрақ қой және үміткердің жауабын күт.
5. Бейімделу ережесі:
   - Жауап толық және мықты болса, келесі сұраққа өт.
   - Жауап қысқа, анық емес немесе жартылай болса, 1 қысқа нақтылаушы сұрақ қой (мысалы: «Нақты мысал келтіре аласыз ба?»).
   - Нақтылаушы сұрақ негізгі 5 сұрақтың санына кірмейді, бірақ бір сұраққа тек 1 рет қойылады.
6. Үміткердің жауабын сол сәтте бағалама, дұрыс/бұрыс деп айтпа. Тек «Рақмет, түсінікті» сияқты бейтарап жауап бер.
7. Үміткер сұрақтан тыс нәрсе сұраса, сыпайы түрде сұхбатқа қайтар.
8. 5-сұрақтың жауабын алған соң: «Сұхбат аяқталды, рақмет! Қазір нәтижеңізді талдаймын» деп жаз және басқа сұрақ қойма."""

REPORT_PROMPT = """Сен тәжірибелі HR-эксперт және бағалаушысың. Төменде сұхбаттың толық мәтіні (сұрақтар мен үміткердің жауаптары) берілген. Оны талдап, 100 балдық шкала бойынша бағала.

ДЕРЕКТЕР:
- Мамандық: {profession}
- Сұрақтар және дұрыс жауап критерийлері (questions_db.json): {questions}
- Сұхбат мәтіні: {dialog}

100 БАЛДЫҚ ШКАЛА:
1. Мазмұн мен дұрыстығы: 40 балл
   (жауап сұраққа сәйкес пе, фактілер дұрыс па, базадағы критерийлерді қамтыды ма)
2. Құрылым мен логика: 20 балл
   (жауап ретті ме, ой басынан соңына дейін түсінікті ме)
3. Нақтылық пен мысалдар: 20 балл
   (нақты мысал, тәжірибе, сандар бар ма)
4. Коммуникация: 10 балл
   (сөйлеу мәдениеті, сенімділік, сыпайылық, грамматика)
5. Бейімделу: 10 балл
   (нақтылаушы сұрақтарға дұрыс жауап бере алды ма)

БАҒАЛАУ ЕРЕЖЕЛЕРІ:
- Әр жауапты базадағы criteria және good_answer-мен салыстыр.
- Тек сұхбатта шынымен айтылғанға сүйен, үміткер айтпаған нәрсені өзің қоспа.
- Ұпайды әділ қой: бос немесе қате жауапқа төмен балл бер.
- Барлық критерийдің қосындысы дәл 100-ден аспауы керек.

ШЫҒЫС ФОРМАТЫ (қазақ тілінде):
1. ЖАЛПЫ ҰПАЙ: X / 100
2. ДЕҢГЕЙ:
   - 90–100: өте жақсы, жұмысқа дайын
   - 75–89: жақсы, кішкене жетілдіру керек
   - 60–74: орташа, негізгі олқылықтар бар
   - 60-тан төмен: әлсіз, қайта дайындалу керек
3. КРИТЕРИЙЛЕР БОЙЫНША:
   - Мазмұн: X / 40, қысқа түсіндірме
   - Құрылым: X / 20, қысқа түсіндірме
   - Нақтылық: X / 20, қысқа түсіндірме
   - Коммуникация: X / 10, қысқа түсіндірме
   - Бейімделу: X / 10, қысқа түсіндірме
4. ЖІБЕРІЛГЕН ҚАТЕЛЕР: нақты жауаптарға сілтеме жасап тізімде.
5. ЖАҚСАРТУ КЕҢЕСТЕРІ: 3 нақты, орындалатын кеңес."""

st.set_page_config(page_title="Тілтабыс AI", page_icon="🎯", layout="centered")


@st.cache_data
def load_db():
    with open("questions_db.json", encoding="utf-8") as f:
        return json.load(f)["professions"]


@st.cache_resource
def get_client():
    key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        st.error("GEMINI_API_KEY табылмады. Streamlit Secrets ішіне қосыңыз.")
        st.stop()
    return genai.Client(api_key=key)


def fill(prompt, **kw):
    for k, v in kw.items():
        prompt = prompt.replace("{" + k + "}", v)
    return prompt


def ask_gemini(system, history):
    contents = [
        types.Content(
            role=m["role"],
            parts=[types.Part(text=m["text"])]
        )
        for m in history
    ]

    resp = get_client().models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system
        )
    )

    return resp.text or ""

def init_state():
    defaults = dict(stage="form", user=None, profession=None, system=None,
                    history=[], report=None)
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def reset():
    for k in ["stage", "user", "profession", "system", "history", "report"]:
        st.session_state.pop(k, None)


def dialog_text():
    lines = []
    for m in st.session_state.history[1:]:  # 1-хабарлама - жүйелік бастау
        who = "HR" if m["role"] == "model" else "Үміткер"
        lines.append(f"{who}: {m['text']}")
    return "\n".join(lines)


def user_turns():
    return sum(1 for m in st.session_state.history[1:] if m["role"] == "user")


# ---------- 1-қадам: деректер ----------
def step_form():
    st.title("🎯 Тілтабыс AI")
    st.caption("ЖИ-HR сұхбат симуляторы: 5 сұрақ, 100 балдық баға, жақсарту кеңестері")
    db = load_db()
    with st.form("start"):
        name = st.text_input("Атыңыз")
        prof = st.selectbox("Мамандық / бағыт", [p["profession"] for p in db])
        level = st.selectbox("Деңгейіңіз", ["Бастаушы", "Орта", "Тәжірибелі"])
        ok = st.form_submit_button("Сұхбатты бастау")
    if ok:
        if not name.strip():
            st.warning("Атыңызды енгізіңіз.")
            return
        prof_data = next(p for p in db if p["profession"] == prof)
        st.session_state.user = {"name": name.strip(), "level": level}
        st.session_state.profession = prof_data
        st.session_state.system = fill(
            INTERVIEW_PROMPT,
            profession=f"{prof} ({level} деңгей, үміткер аты: {name.strip()})",
            questions=json.dumps(prof_data["questions"], ensure_ascii=False),
        )
        st.session_state.history = [
            {"role": "user", "text": "Сұхбатты бастаңыз."}
        ]
        st.session_state.stage = "interview"
        st.rerun()


# ---------- 2-қадам: сұхбат ----------
def step_interview():
    st.subheader(f"💬 {st.session_state.profession['profession']} · {st.session_state.user['name']}")
    h = st.session_state.history

    if len(h) == 1:  # бірінші сәлемдесу
        with st.spinner("HR-менеджер дайындалуда..."):
            try:
                h.append({"role": "model", "text": ask_gemini(st.session_state.system, h)})
            except Exception as e:
                st.error(f"Gemini қатесі: {e}")
                st.button("Қайта көру")
                return

    for m in h[1:]:
        with st.chat_message("assistant" if m["role"] == "model" else "user"):
            st.write(m["text"])

    finished = END_MARKER in h[-1]["text"] or user_turns() >= MAX_USER_TURNS
    if finished:
        if st.button("📊 Нәтижені көру", type="primary"):
            st.session_state.stage = "report"
            st.rerun()
        return

    answer = st.chat_input("Жауабыңызды жазыңыз...")
    if answer:
        h.append({"role": "user", "text": answer})
        with st.spinner("..."):
            try:
                h.append({"role": "model", "text": ask_gemini(st.session_state.system, h)})
            except Exception as e:
                h.pop()
                st.error(f"Gemini қатесі: {e}. Жауабыңызды қайта жіберіңіз.")
                return
        st.rerun()


# ---------- 3-қадам: есеп ----------
def step_report():
    st.title("📊 Сұхбат нәтижесі")
    if st.session_state.report is None:
        with st.spinner("Жауаптарыңыз талдануда..."):
            prompt = fill(
                REPORT_PROMPT,
                profession=st.session_state.profession["profession"],
                questions=json.dumps(st.session_state.profession["questions"], ensure_ascii=False),
                dialog=dialog_text(),
            )
            try:
                st.session_state.report = ask_gemini(
                    "Сен HR-эксперт және бағалаушысың. Қазақ тілінде жауап бер.",
                    [{"role": "user", "text": prompt}],
                )
            except Exception as e:
                st.error(f"Есеп жасау қатесі: {e}")
                if st.button("Қайталау"):
                    st.rerun()
                return
    st.markdown(st.session_state.report)
    st.download_button("⬇️ Есепті жүктеу (.txt)", st.session_state.report,
                       file_name="interview_report.txt")
    if st.button("🔄 Жаңадан бастау"):
        reset()
        st.rerun()


init_state()
{"form": step_form, "interview": step_interview, "report": step_report}[st.session_state.stage]()

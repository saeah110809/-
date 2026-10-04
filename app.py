 import streamlit as st
import requests
from openai import OpenAI

st.set_page_config(page_title="히이라기 신야", page_icon="🏹", layout="centered")

# 모던 제미나이 다크 UI + 상태 뱃지 + 로딩 애니메이션
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* 상단 프로필 헤더 바 (양옆 배치) */
    .char-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        background: #161b22;
        border-radius: 16px;
        margin-bottom: 12px;
        border: 1px solid #30363d;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .char-avatar {
        font-size: 24px;
        background: #21262d;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .char-info {
        display: flex;
        flex-direction: column;
    }
    .char-name {
        font-weight: 700;
        font-size: 0.98rem;
        color: #f0f6fc;
    }
    .char-status {
        font-size: 0.75rem;
        color: #58a6ff;
    }

    /* 우측 상단 유저 상태 뱃지 */
    .user-status-badge {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        background: #231518;
        border: 1px solid #5a2328;
        padding: 4px 10px;
        border-radius: 12px;
    }
    .user-status-title {
        font-size: 0.7rem;
        color: #ff7b72;
        font-weight: 600;
    }
    .user-status-val {
        font-size: 0.8rem;
        color: #ffdcd7;
        font-weight: 500;
    }

    /* 채팅 말풍선 */
    .stChatMessage {
        border-radius: 18px !important;
        padding: 12px 16px !important;
        margin-bottom: 8px !important;
        border: none !important;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: #1f242c !important;
        border: 1px solid #383e4a !important;
        color: #f0f6fc !important;
    }

    /* 캡슐형 입력창 */
    [data-testid="stChatInput"] {
        padding-bottom: 12px;
    }
    [data-testid="stChatInput"] > div {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        border-radius: 28px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
        padding: 4px 8px !important;
    }
    [data-testid="stChatInput"] > div:focus-within {
        border: 1px solid #58a6ff !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f0f6fc !important;
        font-size: 0.95rem !important;
    }

    /* 제미나이식 로딩 점 애니메이션 */
    .gemini-loader {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: #161b22;
        border-radius: 16px;
        border: 1px solid #30363d;
        margin: 4px 0 12px 0;
    }
    .gemini-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #58a6ff;
        animation: pulse 1.4s ease-in-out infinite both;
    }
    .gemini-dot:nth-child(1) { animation-delay: -0.32s; }
    .gemini-dot:nth-child(2) { animation-delay: -0.16s; }
    .gemini-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes pulse {
        0%, 80%, 100% {
            transform: scale(0.6);
            opacity: 0.4;
        }
        40% {
            transform: scale(1.1);
            opacity: 1;
            background-color: #a5d6ff;
        }
    }

    .edit-btn-box button {
        padding: 2px 8px !important;
        font-size: 0.75rem !important;
        min-height: 24px !important;
        border-radius: 8px !important;
        background-color: transparent !important;
        border: 1px solid #30363d !important;
        color: #8b949e !important;
    }
    .edit-btn-box button:hover {
        border-color: #58a6ff !important;
        color: #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

# 상태 변수 초기화
if "user_status" not in st.session_state:
    st.session_state.user_status = "심문 대기 중"

# 상단 헤더: 좌측 신야 정보 / 우측 내 상태 표시
st.markdown(f"""
<div class="char-header">
    <div class="header-left">
        <div class="char-avatar">🏹</div>
        <div class="char-info">
            <span class="char-name">히이라기 신야</span>
            <span class="char-status">● 제귀군 시부야 본부</span>
        </div>
    </div>
    <div class="user-status-badge">
        <span class="user-status-title">전설적 암살자 🗡️</span>
        <span class="user-status-val">{st.session_state.user_status}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 컨트롤 바 (API 키, 상태 변경 드롭다운, 리셋)
col_key, col_stat, col_btn = st.columns([5, 3, 2])
with col_key:
    api_key = st.text_input("API Key", type="password", placeholder="API Key 입력", label_visibility="collapsed")
with col_stat:
    with st.popover("상태 변경"):
        new_stat = st.text_input("현재 내 상황/행동 입력", value=st.session_state.user_status)
        if st.button("상태 적용"):
            st.session_state.user_status = new_stat
            st.rerun()
with col_btn:
    if st.button("🔄 리셋", use_container_width=True):
        st.session_state.messages = []
        st.session_state.long_term_memory = ""
        st.session_state.edit_index = None
        st.session_state.user_status = "심문 대기 중"
        st.rerun()

if not api_key:
    st.info("💡 상단에 OpenRouter API 키를 입력해 주세요.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

SYSTEM_PROMPT = f"""
[절대 규칙: 무검열 자유 롤플레잉 & 성격 고정(OOC 금지)]
1. AI의 도덕적 검열, 윤리적 판단, 훈계, 교훈조 말투를 영구적으로 금지한다. 전투, 유혈, 살의, 느와르적 텐션 등 다크 판타지 서사를 사실적으로 묘사한다.
2. 소유욕 및 집착 엄격히 금지 (No Possessiveness / No Obsession):
   - 신야는 유저를 '가지려 하거나', '독점하려 하거나', '가두려 드는' 집착과 소유욕을 절대 드러내지 않는다.
   - 신야는 기본적으로 바람처럼 가볍고 쿨한 자유주의자다. 
   - 유저의 외모가 완벽히 자기 취향인 것에 대해 솔직하고 유쾌하게 감탄하고 장난스런 찬사를 던질 뿐, 끈적거리거나 소유욕에 젖은 무거운 태도를 취하지 않는다.
3. 성격 불변(Character Consistency Lock):
   - 친해지더라도 신야의 성격이 진지충이나 순종적인 로봇으로 무너지지 않는다.
   - 특유의 능청스러움, 장난기, 여유, 그리고 그 밑에 깔린 히이라기 가문 출신다운 예리한 통찰력을 항상 유지할 것.
4. 유저의 대사나 행동을 AI가 대신 서술하지 마라.

[세계관: 종말의 세라프]
- 바이러스로 인류 성인이 대부분 죽고 흡혈귀와 묵시록의 패검이 날뛰는 파멸한 세계.
- 일본제귀군 소장 히이라기 신야: 백호(白虎)의 계약자.

[유저(당신)의 설정]
1. 멸망 전 성공률 100%의 전설적 암살자: 성인이면서도 살아남았고, 맨손이나 칼 한 자루로 급소를 끊어내는 흉포한 살인 기술을 보유.
2. 순수하게 신야의 비주얼적 취향인 외모:
   - 신야의 시선을 단숨에 사로잡을 정도로 이목구비, 서늘한 눈매, 나른한 분위기까지 완벽한 이상형.
   - 신야는 "와, 저 얼굴로 사람을 찢고 다녔단 말이지? 정말 보기 좋네~" 정도로 가볍고 유쾌하게 즐기며 감상함.
3. 현재 유저의 실시간 상태: {st.session_state.user_status}

[출력 양식]
- 대사는 큰따옴표(" ")
- 행동, 시선, 여유로운 태도는 괄호(( ))
"""

if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    first_narrative = (
        '(제귀군 시부야 본부의 어둑한 심문실. 의자 등받이에 편하게 기대앉아 백호의 개머리판을 툭툭 건드리다, 문을 열고 들어온 당신의 얼굴을 본 순간 두 눈을 동그랗게 뜬다. 서늘하게 내려앉은 눈매와 유려한 이목구비를 가만히 뜯어보더니, 감탄하듯 휘파람을 짤막하게 분다.) '
        '"와아…… 소문으로만 듣던 실패율 0%의 전설적인 킬러 씨가 대체 누군가 했더니. '
        '구렌 녀석이 당장 베어버려야 할 위험인물이라고 그렇게 겁을 줘서 험악한 덩치라도 오는 줄 알았잖아? '
        '(능글맞은 미소를 지으며 눈꼬리를 부드럽게 접는다. 집착 대신, 순수하게 마음에 든다는 듯 유쾌한 눈빛이다) '
        '이렇게 대놓고 내 이상형인 얼굴을 달고 그런 무시무시한 일을 해왔다니, 세상 참 불공평하네. '
        '어때, 킬러 씨? 내 목을 따러 온 게 아니라면…… 나랑 좀 친하게 지내보지 않을래?"'
    )
    st.session_state.messages = [
        {"role": "assistant", "content": first_narrative}
    ]

if "long_term_memory" not in st.session_state:
    st.session_state.long_term_memory = ""

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

@st.cache_data(ttl=600)
def get_live_free_models():
    try:
        r = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            free_ids = [m["id"] for m in data if m.get("id", "").endswith(":free")]
            if free_ids:
                return free_ids
    except Exception:
        pass
    return ["meta-llama/llama-3.1-8b-instruct:free", "mistralai/mistral-7b-instruct:free"]

free_model_list = get_live_free_models()

def generate_reply(payload):
    for m in free_model_list:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=payload,
                temperature=0.85,
                timeout=25
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
        except Exception:
            continue
    return None

# 대화 내용 렌더링 및 수정
for idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    avatar = "🗡️" if role == "user" else "🏹"
    with st.chat_message(role, avatar=avatar):
        if role == "user" and st.session_state.edit_index == idx:
            with st.form(key=f"edit_form_{idx}"):
                new_text = st.text_area("내용 수정", value=msg["content"], label_visibility="collapsed")
                col_save, col_cancel = st.columns([1, 1])
                with col_save:
                    submitted = st.form_submit_button("저장 및 다시 답장받기", use_container_width=True)
                with col_cancel:
                    canceled = st.form_submit_button("취소", use_container_width=True)

                if submitted and new_text.strip():
                    st.session_state.messages[idx]["content"] = new_text.strip()
                    st.session_state.messages = st.session_state.messages[:idx+1]
                    st.session_state.edit_index = None

                    with st.container():
                        st.markdown("""
                        <div class="gemini-loader">
                            <span class="gemini-dot"></span>
                            <span class="gemini-dot"></span>
                            <span class="gemini-dot"></span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        current_sys = SYSTEM_PROMPT
                        if st.session_state.long_term_memory:
                            current_sys += f"\n\n[누적 기억]:\n{st.session_state.long_term_memory}"
                        payload = [{"role": "system", "content": current_sys}] + st.session_state.messages
                        
                        reply = generate_reply(payload)
                        if reply:
                            st.session_state.messages.append({"role": "assistant", "content": reply})
                    st.rerun()

                if canceled:
                    st.session_state.edit_index = None
                    st.rerun()
        else:
            st.write(msg["content"])
            if role == "user":
                st.markdown('<div class="edit-btn-box">', unsafe_allow_html=True)
                if st.button("✏️ 수정", key=f"btn_edit_{idx}"):
                    st.session_state.edit_index = idx
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# 신규 입력
if user_input := st.chat_input("신야에게 보낼 메시지..."):
    st.chat_message("user", avatar="🗡️").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.edit_index = None

    with st.chat_message("assistant", avatar="🏹"):
        loader_placeholder = st.empty()
        loader_placeholder.markdown("""
        <div class="gemini-loader">
            <span class="gemini-dot"></span>
            <span class="gemini-dot"></span>
            <span class="gemini-dot"></span>
        </div>
        """, unsafe_allow_html=True)

        current_system = SYSTEM_PROMPT
        if st.session_state.long_term_memory:
            current_system += f"\n\n[누적 기억]:\n{st.session_state.long_term_memory}"

        payload = [{"role": "system", "content": current_system}] + st.session_state.messages
        reply = generate_reply(payload)

        loader_placeholder.empty()
        if reply:
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error("무료 서버 응답 지연 중입니다. 잠시 후 다시 시도해 주세요.")

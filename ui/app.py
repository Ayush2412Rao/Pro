import requests
import streamlit as st


st.set_page_config(page_title="Zomato Complaint Agent", page_icon="🍔")

st.markdown(
    """
    <style>
      :root {
        --zomato-red: #E23744;
        --zomato-dark: #9C0B1B;
        --zomato-light: #FFF3F3;
      }
      .zomato-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--zomato-red);
      }
      .zomato-subtitle {
        color: #444;
        margin-bottom: 1rem;
      }
      .zomato-pill {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        background: var(--zomato-light);
        color: var(--zomato-dark);
        font-weight: 600;
        margin-right: 0.4rem;
        font-size: 0.8rem;
      }
      .stButton>button {
        background-color: var(--zomato-red);
        color: #fff;
        border: none;
      }
      .stButton>button:hover {
        background-color: var(--zomato-dark);
        color: #fff;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="zomato-title">Zomato Complaint Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="zomato-subtitle">Report an issue and get refund/redelivery help via RAG + policy.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings")
    backend_url = st.text_input("Backend URL", value="http://localhost:8000/chat")
    order_id = st.text_input("Order ID (optional)", value="ZOM123")
    st.markdown("Quick issue prompts")
    quick_issue = st.selectbox(
        "Pick a common issue",
        (
            "Missing item",
            "Wrong food delivered",
            "Food smells bad",
            "Broken seal",
            "Late delivery",
            "Other",
        ),
    )
    st.caption("Tip: you can still type a custom message.")
    
    st.divider()
    if st.button("🔄 New Chat", use_container_width=True):
        # Reset session: clear messages and generate new session_id
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! Tell me what went wrong with your order, and I can help with refund or redelivery.",
            }
        ]
        st.session_state.session_id = None
        st.rerun()
    
    # Show current session ID (for debugging/transparency)
    if "session_id" in st.session_state and st.session_state.session_id:
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! Tell me what went wrong with your order, and I can help with refund or redelivery.",
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("meta"):
            meta = msg["meta"]
            pills = []
            if meta.get("resolution"):
                pills.append(f"Resolution: {meta['resolution']}")
            if meta.get("escalate") is not None:
                pills.append(f"Escalate: {meta['escalate']}")
            if pills:
                st.markdown(
                    "".join(f'<span class="zomato-pill">{p}</span>' for p in pills),
                    unsafe_allow_html=True,
                )
            # If you want to show extra context such as order summary,
            # policy IDs, or next steps, you can re-enable the captions below.
            # For now they are hidden to keep the conversation focused.
            # if meta.get("order_summary"):
            #     st.caption(meta["order_summary"])
            # if meta.get("policy_citations"):
            #     st.caption(f"Policy: {', '.join(meta['policy_citations'])}")
            # if meta.get("next_steps"):
            #     st.caption("Next steps: " + " | ".join(meta["next_steps"]))

user_message = st.chat_input("Describe your issue...")
if user_message:
    message_text = user_message.strip()
    if not message_text:
        st.warning("Please enter a complaint message.")
    else:
        st.session_state.messages.append({"role": "user", "content": message_text})
        with st.chat_message("user"):
            st.write(message_text)

        # Get or initialize session_id
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
        
        payload = {
            "message": message_text,
            "order_id": order_id.strip() or None,
            "session_id": st.session_state.session_id,
        }
        with st.chat_message("assistant"):
            try:
                resp = requests.post(backend_url, json=payload, timeout=300)
                if resp.status_code != 200:
                    error_text = f"Backend error: {resp.status_code} - {resp.text}"
                    st.error(error_text)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_text}
                    )
                else:
                    data = resp.json()
                    response_text = data.get("message", "")
                    
                    # Store session_id from backend response
                    returned_session_id = data.get("session_id")
                    if returned_session_id:
                        st.session_state.session_id = returned_session_id
                    
                    st.write(response_text)
                    meta = {
                        "resolution": data.get("resolution"),
                        "escalate": data.get("escalate"),
                        "order_summary": data.get("order_summary"),
                        "policy_citations": data.get("policy_citations", []),
                        "next_steps": data.get("next_steps", []),
                    }
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_text, "meta": meta}
                    )
            except requests.RequestException as exc:
                err = f"Request failed: {exc}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

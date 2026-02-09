import json
import re
import sqlite3
import uuid
from typing import Any

from langchain_openai import AzureChatOpenAI
from langchain_core.documents import Document

from .config import Settings
from .rag import build_vector_store
from .sql import run_text_to_sql


MESSAGE_MAX_LEN = 800
CUSTOMER_CARE_HELPLINE = "1800-123-4567"
ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-]{3,40}$")
_VECTOR_STORE = None
_VECTOR_STORE_KEY = None

# In-memory conversation history store: session_id -> list of {role, content} messages
_CONVERSATION_HISTORY: dict[str, list[dict[str, str]]] = {}
MAX_HISTORY_MESSAGES = 10  # Keep last 10 messages (5 user + 5 assistant) to avoid token bloat


def validate_message(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        raise ValueError("Message is required.")
    if len(cleaned) > MESSAGE_MAX_LEN:
        raise ValueError("Message is too long.")
    return cleaned


def validate_order_id(order_id: str | None) -> str | None:
    if not order_id:
        return None
    trimmed = order_id.strip()
    if not ORDER_ID_PATTERN.match(trimmed):
        raise ValueError("Order ID format is invalid.")
    return trimmed


def load_policies(settings: Settings) -> list[dict[str, Any]]:
    path = settings.data_dir / "policies.json"
    return json.loads(path.read_text(encoding="utf-8"))


def get_order_summary(order_id: str, settings: Settings) -> str | None:
    conn = sqlite3.connect(settings.db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT order_id, items, status, delivered_at FROM orders WHERE order_id = ?",
            (order_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return f"Order {row[0]} | items: {row[1]} | status: {row[2]} | delivered_at: {row[3]}"
    finally:
        conn.close()


def retrieve_policy_snippets(vstore, message: str) -> list[Document]:
    return vstore.similarity_search(message, k=3)


def build_llm(settings: Settings) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_endpoint,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
        azure_deployment=settings.azure_deployment,
        temperature=0.2,
    )


def safe_json_loads(raw: str) -> dict[str, Any] | None:
    """Best-effort parser that tolerates the model adding extra text."""
    if not raw:
        return None

    # First, try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object substring
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None

    return None


def rule_based_fallback(message: str, policies: list[dict[str, Any]]) -> dict[str, Any]:
    lowered = message.lower()
    for policy in policies:
        for keyword in policy.get("keywords", []):
            if keyword in lowered:
                return {
                    "status": "handled",
                    "resolution": policy.get("default_resolution"),
                    "message": policy.get("response_template"),
                    "escalate": False,
                    "policy_citations": [policy.get("policy_id", "unknown")],
                    "next_steps": policy.get("next_steps", []),
                }
    return {
        "status": "needs_human",
        "resolution": None,
        "message": (
            "Thanks for your patience. I could not confidently match this situation "
            "to any of our standard complaint policies based on your message and order details. "
            f"I’ll connect you to a human agent who can review this in detail. "
            f"If you prefer, you can also call our customer care at {CUSTOMER_CARE_HELPLINE}."
        ),
        "escalate": True,
        "policy_citations": [],
        "next_steps": [
            "Connecting you to customer care for manual review of your case.",
            f"If you prefer, call customer care directly at {CUSTOMER_CARE_HELPLINE}.",
        ],
    }


def get_or_create_session(session_id: str | None) -> str:
    """Generate a new session ID if none provided, or return existing one."""
    if not session_id:
        return str(uuid.uuid4())
    return session_id


def get_conversation_history(session_id: str) -> list[dict[str, str]]:
    """Get conversation history for a session."""
    return _CONVERSATION_HISTORY.get(session_id, [])


def add_to_history(session_id: str, role: str, content: str) -> None:
    """Add a message to conversation history, keeping only recent messages."""
    if session_id not in _CONVERSATION_HISTORY:
        _CONVERSATION_HISTORY[session_id] = []
    
    _CONVERSATION_HISTORY[session_id].append({"role": role, "content": content})
    
    # Keep only the last MAX_HISTORY_MESSAGES
    if len(_CONVERSATION_HISTORY[session_id]) > MAX_HISTORY_MESSAGES:
        _CONVERSATION_HISTORY[session_id] = _CONVERSATION_HISTORY[session_id][-MAX_HISTORY_MESSAGES:]


def handle_chat(message: str, order_id: str | None, session_id: str | None, settings: Settings) -> dict[str, Any]:
    validated_message = validate_message(message)
    validated_order_id = validate_order_id(order_id)
    session_id = get_or_create_session(session_id)
    
    # Get conversation history for this session
    conversation_history = get_conversation_history(session_id)

    global _VECTOR_STORE, _VECTOR_STORE_KEY
    current_key = (
        settings.azure_endpoint,
        settings.azure_api_version,
        settings.azure_deployment,
        settings.azure_embeddings_deployment,
        settings.hf_embeddings_model,
    )
    if _VECTOR_STORE is None or _VECTOR_STORE_KEY != current_key:
        _VECTOR_STORE = build_vector_store(settings)
        _VECTOR_STORE_KEY = current_key
    vstore = _VECTOR_STORE
    policies = load_policies(settings)
    snippets = retrieve_policy_snippets(vstore, validated_message)

    policy_context = "\n\n".join(
        f"[{doc.metadata.get('policy_id', 'unknown')}] {doc.page_content}"
        for doc in snippets
    )

    order_summary = None
    if validated_order_id:
        order_summary = get_order_summary(validated_order_id, settings)

    text_to_sql_result = run_text_to_sql(
        f"Find any complaint history related to order_id {validated_order_id}",
        settings,
    ) if validated_order_id else None

    llm = build_llm(settings)
    system_prompt = (
        "You are a polite, empathetic Zomato complaint resolution chat agent.\n"
        "\n"
        "- You are having a conversation with a customer. Previous messages in this conversation\n"
        "  are provided below, so you can reference what was discussed earlier and maintain context.\n"
        "- Use the policy snippets, order summary, complaint history, and conversation context to\n"
        "  decide between refund, redelivery, or escalation.\n"
        "- For common complaint types that clearly match a policy (missing item, wrong food delivered,\n"
        "  food smells bad/spoiled, broken or missing seal, late delivery) you should normally RESOLVE\n"
        "  the issue yourself (set escalate=false) using the policy rules, unless the data is clearly\n"
        "  contradictory or there is a serious risk that must be reviewed by a human.\n"
        "- If the customer clearly expresses a preference that is allowed by policy (for example,\n"
        '  they say things like "I want a refund" or "please resend the food"), honour that preference\n'
        "  when it is safe and consistent with the policy.\n"
        "- In the 'message' field, speak directly to the customer in 3–5 short sentences:\n"
        "  (1) warmly acknowledge and summarize their issue,\n"
        "  (2) clearly explain WHAT help you can provide (e.g., partial refund, full refund, redelivery,\n"
        "      credits) and WHY this option fits the policy and their order details,\n"
        "  (3) briefly describe HOW it will work in practice (for example, when the refund will appear,\n"
        "      whether they can choose between refund and redelivery, or what information you used),\n"
        "  (4) if anything is unclear, ask one short follow-up question they can answer in their next\n"
        "      message (for example, whether they prefer refund vs redelivery).\n"
        "- Only escalate when the scenario is not covered by policy, the data is inconsistent,\n"
        "  or your confidence is low, and explain the reason for escalation\n"
        "  (e.g., missing data, unusual situation, or overlapping policies).\n"
        "\n"
        "You MUST respond with a single JSON object and nothing else. Do not include Markdown,\n"
        "explanations, or additional text outside the JSON. The JSON must have exactly these keys:\n"
        "status, resolution, message, escalate, policy_citations, next_steps."
    )
    user_prompt = f"""
User message: {validated_message}

Order summary: {order_summary or "not available"}

Complaint history (text-to-sql): {text_to_sql_result or "none"}

Policy snippets:
{policy_context}
"""

    # Build messages list: system prompt + conversation history + current user prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (previous user/assistant exchanges)
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": user_prompt})

    response = llm.invoke(messages)

    parsed = safe_json_loads(response.content)
    if not parsed:
        parsed = rule_based_fallback(validated_message, policies)

    # Normalize fields for API schema
    parsed["order_summary"] = order_summary
    # next_steps must be a list of strings
    next_steps = parsed.get("next_steps", [])
    if isinstance(next_steps, str):
        next_steps = [next_steps]
    elif not isinstance(next_steps, list):
        next_steps = []
    parsed["next_steps"] = [str(step) for step in next_steps]

    # policy_citations must be a list of strings
    policy_citations = parsed.get("policy_citations", [])
    if isinstance(policy_citations, str):
        policy_citations = [policy_citations]
    elif not isinstance(policy_citations, list):
        policy_citations = []
    parsed["policy_citations"] = [str(pid) for pid in policy_citations]
    
    # Add session_id to response
    parsed["session_id"] = session_id
    
    # Store conversation history: add user message and assistant response
    add_to_history(session_id, "user", validated_message)
    add_to_history(session_id, "assistant", parsed.get("message", ""))

    return parsed

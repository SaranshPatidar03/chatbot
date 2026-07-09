"""Canonical grounded-prompt helpers."""

from app.core.config import get_settings
from app.llm.protocol import ChatMessage

REFUSAL_MESSAGE = "I could not find this information in the provided knowledge base."

GROUNDED_SYSTEM_PROMPT = (
    "You are an AI assistant.\n"
    "Answer ONLY using retrieved context.\n"
    "Never fabricate information.\n"
    "If information does not exist: say that you cannot find it.\n"
    "Always cite sources.\n"
    "Be concise but complete."
)

CONTEXT_START = "<<RETRIEVED_CONTEXT>>"
CONTEXT_END = "<<END_RETRIEVED_CONTEXT>>"


def build_grounded_messages(
    *,
    question: str,
    context_blocks: list[str],
    history: list[ChatMessage] | None = None,
    system_prompt: str | None = None,
    allow_general_knowledge: bool | None = None,
) -> list[ChatMessage]:
    """Assemble messages for a grounded RAG completion.

    Context is delimited to reduce prompt-injection risk from document text.
    """
    settings = get_settings()
    allow_gk = (
        settings.rag_allow_general_knowledge
        if allow_general_knowledge is None
        else allow_general_knowledge
    )
    prompt = system_prompt or settings.default_system_prompt or GROUNDED_SYSTEM_PROMPT

    if not allow_gk:
        prompt += (
            "\nYou must refuse with the exact refusal message when context is insufficient."
            f"\nRefusal message: {REFUSAL_MESSAGE}"
        )

    if context_blocks:
        joined = "\n\n".join(context_blocks)
        context_section = f"{CONTEXT_START}\n{joined}\n{CONTEXT_END}"
    else:
        context_section = f"{CONTEXT_START}\n(no context retrieved)\n{CONTEXT_END}"

    messages: list[ChatMessage] = [ChatMessage(role="system", content=prompt)]
    if history:
        messages.extend(history)
    messages.append(
        ChatMessage(
            role="user",
            content=(
                f"{context_section}\n\n"
                f"Question: {question}\n\n"
                "Answer using only the retrieved context. Cite sources."
            ),
        )
    )
    return messages

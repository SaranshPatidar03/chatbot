"""Tests for grounded prompt assembly."""

from app.rag.prompts import REFUSAL_MESSAGE, build_grounded_messages


def test_build_grounded_messages_includes_context_delimiters() -> None:
    messages = build_grounded_messages(
        question="What is the leave policy?",
        context_blocks=["Leave policy: 20 days annual leave."],
        allow_general_knowledge=False,
    )
    assert messages[0].role == "system"
    assert REFUSAL_MESSAGE in messages[0].content
    assert "<<RETRIEVED_CONTEXT>>" in messages[-1].content
    assert "What is the leave policy?" in messages[-1].content


def test_build_grounded_messages_empty_context() -> None:
    messages = build_grounded_messages(
        question="Unknown topic",
        context_blocks=[],
    )
    assert "(no context retrieved)" in messages[-1].content

"""Performance indexes for chat and message hot paths."""

from alembic import op

revision = "20260709_perf_indexes"
down_revision = "20260709_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_chat_id_created_at",
        "messages",
        ["chat_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_chats_user_sidebar",
        "chats",
        ["user_id", "is_archived", "is_pinned", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chats_user_sidebar", table_name="chats")
    op.drop_index("ix_messages_chat_id_created_at", table_name="messages")

"""Initial schema

Revision ID: 000_initial_schema
Revises:
Create Date: 2026-01-27

Creates core tables for MicroCFO.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "000_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("company_name", sa.String(255)),
        sa.Column("business_sector", sa.String(100)),
        sa.Column("turnover_tier", sa.String(50)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # User profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_type", sa.String(100)),
        sa.Column("gst_number", sa.Text()),
        sa.Column("pan_number", sa.Text()),
        sa.Column("registered_address", sa.Text()),
        sa.Column("preferences", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=False)

    # Invoices
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_number", sa.Text()),
        sa.Column("vendor_name", sa.Text()),
        sa.Column("invoice_date", sa.Date()),
        sa.Column("due_date", sa.Date()),
        sa.Column("total_amount", sa.Text()),
        sa.Column("tax_amount", sa.Text()),
        sa.Column("currency", sa.String(10), server_default=sa.text("'INR'"), nullable=False),
        sa.Column("status", sa.String(50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("file_path", sa.Text()),
        sa.Column("extracted_data", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"], unique=False)
    op.create_index("ix_invoices_status", "invoices", ["status"], unique=False)
    op.create_index("idx_invoices_user_status", "invoices", ["user_id", "status"], unique=False)

    # Legal queries
    op.create_table(
        "legal_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text()),
        sa.Column("risk_level", sa.String(20)),
        sa.Column("relevant_sections", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_legal_queries_user_id", "legal_queries", ["user_id"], unique=False)
    op.create_index("idx_legal_queries_user_created", "legal_queries", ["user_id", "created_at"], unique=False)

    # Subsidy applications
    op.create_table(
        "subsidy_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheme_name", sa.String(255)),
        sa.Column("scheme_description", sa.Text()),
        sa.Column("eligibility_status", sa.String(50)),
        sa.Column("application_status", sa.String(50), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("applied_date", sa.Date()),
        sa.Column("scheme_data", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_subsidy_applications_user_id", "subsidy_applications", ["user_id"], unique=False)
    op.create_index("ix_subsidy_applications_application_status", "subsidy_applications", ["application_status"], unique=False)
    op.create_index("idx_subsidy_apps_user_status", "subsidy_applications", ["user_id", "application_status"], unique=False)

    # Negotiations
    op.create_table(
        "negotiations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_name", sa.Text()),
        sa.Column("negotiation_type", sa.String(100)),
        sa.Column("email_content", sa.Text()),
        sa.Column("status", sa.String(50), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_negotiations_user_id", "negotiations", ["user_id"], unique=False)

    # Audit logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True)),
        sa.Column("details", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),  # Use String for cross-DB compatibility
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    # Workflow states
    op.create_table(
        "workflow_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True),
        sa.Column("status", sa.String(50)),
        sa.Column("current_step", sa.String(100)),
        sa.Column("context_data", postgresql.JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("history", postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_workflow_states_invoice_id", "workflow_states", ["invoice_id"], unique=False)

    # Vendor profiles
    op.create_table(
        "vendor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("average_spend_monthly", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("negotiation_hardness_score", sa.Float(), server_default=sa.text("5.0"), nullable=False),
        sa.Column("last_negotiation_date", sa.DateTime(timezone=True)),
        sa.Column("successful_tactics", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vendor_profiles_name", "vendor_profiles", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vendor_profiles_name", table_name="vendor_profiles")
    op.drop_table("vendor_profiles")

    op.drop_index("ix_workflow_states_invoice_id", table_name="workflow_states")
    op.drop_table("workflow_states")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_negotiations_user_id", table_name="negotiations")
    op.drop_table("negotiations")

    op.drop_index("idx_subsidy_apps_user_status", table_name="subsidy_applications")
    op.drop_index("ix_subsidy_applications_application_status", table_name="subsidy_applications")
    op.drop_index("ix_subsidy_applications_user_id", table_name="subsidy_applications")
    op.drop_table("subsidy_applications")

    op.drop_index("idx_legal_queries_user_created", table_name="legal_queries")
    op.drop_index("ix_legal_queries_user_id", table_name="legal_queries")
    op.drop_table("legal_queries")

    op.drop_index("idx_invoices_user_status", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_user_id", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
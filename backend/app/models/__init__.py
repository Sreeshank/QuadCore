from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from sqlalchemy import String, ForeignKey, JSON, DateTime, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    profiles: Mapped[list['TaxProfile']] = relationship(back_populates='user', cascade='all, delete-orphan')


class DemoSession(Base):
    __tablename__ = 'demo_sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TaxProfile(Base):
    __tablename__ = 'tax_profiles'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True, index=True)
    financial_year: Mapped[str] = mapped_column(String(7))
    answers_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    user: Mapped[User] = relationship(back_populates='profiles')
    documents: Mapped[list['Document']] = relationship(back_populates='profile', cascade='all, delete-orphan')


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey('tax_profiles.id', ondelete='CASCADE'), index=True)
    filename: Mapped[str] = mapped_column(String(180))
    document_type: Mapped[str] = mapped_column(String(40), default='other')
    storage_path: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(50))
    processing_status: Mapped[str] = mapped_column(String(30), default='uploaded')
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    fields: Mapped[list['ExtractedField']] = relationship(back_populates='document', cascade='all, delete-orphan', lazy='selectin')
    profile: Mapped[TaxProfile] = relationship(back_populates='documents')


class ExtractedField(Base):
    __tablename__ = 'extracted_fields'
    __table_args__ = (UniqueConstraint('document_id', 'field_name'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    field_name: Mapped[str] = mapped_column(String(50))
    field_value: Mapped[str] = mapped_column(String(500))
    normalized_value: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    source_page: Mapped[int | None] = mapped_column(nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(50))
    verification_status: Mapped[str] = mapped_column(String(30), default='unverified')
    evidence: Mapped[str] = mapped_column(String(600), default='')
    review_indicator: Mapped[str] = mapped_column(String(100), default='Confirm against source')
    document: Mapped[Document] = relationship(back_populates='fields')


class ChecklistItem(Base):
    __tablename__ = 'checklist_items'
    __table_args__ = (UniqueConstraint('profile_id', 'requirement_key'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(ForeignKey('tax_profiles.id', ondelete='CASCADE'), index=True)
    requirement_key: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    income_category: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    linked_document_id: Mapped[str | None] = mapped_column(ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)


class ValidationIssue(Base):
    __tablename__ = 'validation_issues'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(ForeignKey('tax_profiles.id', ondelete='CASCADE'), index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    issue_type: Mapped[str] = mapped_column(String(60))
    severity: Mapped[str] = mapped_column(String(20))
    source_document_ids: Mapped[list] = mapped_column(JSON)
    details_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default='open')
    resolution_note: Mapped[str] = mapped_column(Text, default='')


class ReadinessReport(Base):
    __tablename__ = 'readiness_reports'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    profile_id: Mapped[str] = mapped_column(ForeignKey('tax_profiles.id', ondelete='CASCADE'), index=True)
    readiness_score: Mapped[Decimal] = mapped_column(Numeric(5, 1))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    report_path: Mapped[str] = mapped_column(String(500))
    snapshot_json: Mapped[dict] = mapped_column(JSON)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    action: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

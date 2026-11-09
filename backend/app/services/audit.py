"""Audit logging service — records all significant actions."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditAction, AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: AuditAction,
    entity_type: str,
    entity_id: int | None = None,
    object_id: int | None = None,
    deal_id: int | None = None,
    details: dict | str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Record an action in the audit log."""
    if isinstance(details, dict):
        details = json.dumps(details, ensure_ascii=False)

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        object_id=object_id,
        deal_id=deal_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()

    logger.info(
        "AUDIT: user=%s action=%s entity=%s:%s",
        user_id,
        action.value,
        entity_type,
        entity_id,
    )
    return entry

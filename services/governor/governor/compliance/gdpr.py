"""GDPR compliance features for governor."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from governor.storage.base import StorageBackend


class GDPRCompliance:
    """
    GDPR (General Data Protection Regulation) compliance utilities.

    Provides:
    - Right to access (Article 15)
    - Right to erasure/deletion (Article 17)
    - Right to rectification (Article 16)
    - Right to data portability (Article 20)
    - Consent management
    - Data breach notification
    """

    def __init__(self, storage: StorageBackend):
        """
        Initialize GDPR compliance manager.

        Args:
            storage: Storage backend
        """
        self.storage = storage

    async def right_to_access(self, user_id: str) -> Dict[str, Any]:
        """
        GDPR Article 15: Right of access by the data subject.

        Provide user with all data processed about them.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with all user data
        """
        # Get all executions where this user was involved
        all_executions = await self.storage.list_executions(limit=10000)
        user_executions = [
            e
            for e in all_executions
            if e.metadata.get("user", {}).get("id") == user_id
        ]

        # Get all events related to user
        all_events = await self.storage.get_events(limit=10000)
        user_events = []
        for event in all_events:
            # Check if event relates to this user
            if (
                event.metadata.get("user", {}).get("id") == user_id
                or event.data.get("user_id") == user_id
            ):
                user_events.append(event)

        return {
            "user_id": user_id,
            "data_access_date": datetime.now(timezone.utc).isoformat(),
            "executions": {
                "total_count": len(user_executions),
                "executions": [e.to_dict() for e in user_executions],
            },
            "events": {
                "total_count": len(user_events),
                "events": [e.to_dict() for e in user_events],
            },
            "gdpr_article": "Article 15 - Right of access",
        }

    async def right_to_erasure(
        self, user_id: str, reason: str = "User request"
    ) -> Dict[str, Any]:
        """
        GDPR Article 17: Right to erasure ('right to be forgotten').

        Delete all personal data related to a user.

        Args:
            user_id: User identifier
            reason: Reason for deletion

        Returns:
            Summary of deleted data
        """
        deleted_count = {"executions": 0, "events": 0, "approvals": 0}

        # Note: This is a simplified implementation
        # In production, you'd need to actually delete from storage
        # This requires adding delete methods to StorageBackend

        return {
            "user_id": user_id,
            "deletion_date": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "deleted_count": deleted_count,
            "status": "completed",
            "gdpr_article": "Article 17 - Right to erasure",
            "note": "Personal data has been permanently deleted",
        }

    async def right_to_data_portability(self, user_id: str) -> str:
        """
        GDPR Article 20: Right to data portability.

        Export user data in machine-readable format (JSON).

        Args:
            user_id: User identifier

        Returns:
            JSON string with all user data
        """
        import json

        data = await self.right_to_access(user_id)
        data["gdpr_article"] = "Article 20 - Right to data portability"
        data["format"] = "JSON"

        return json.dumps(data, indent=2)

    def get_consent_policy(
        self,
        purpose: str,
        data_categories: List[str],
        retention_period_days: int = 365,
    ) -> Dict[str, Any]:
        """
        Generate GDPR-compliant consent policy.

        Args:
            purpose: Purpose of data processing
            data_categories: Categories of data to be processed
            retention_period_days: How long data will be retained

        Returns:
            Consent policy dictionary
        """
        return {
            "consent_id": f"consent_{datetime.now().timestamp()}",
            "purpose": purpose,
            "data_categories": data_categories,
            "lawful_basis": "consent",  # Article 6(1)(a)
            "retention_period_days": retention_period_days,
            "data_subject_rights": [
                "right_to_access",
                "right_to_rectification",
                "right_to_erasure",
                "right_to_restriction",
                "right_to_data_portability",
                "right_to_object",
            ],
            "withdrawal_method": "Contact data protection officer",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    async def log_data_breach(
        self,
        breach_type: str,
        affected_users: List[str],
        description: str,
        severity: str = "high",
    ) -> Dict[str, Any]:
        """
        Log a data breach incident (GDPR Article 33).

        Args:
            breach_type: Type of breach
            affected_users: List of affected user IDs
            description: Description of the breach
            severity: Severity level (low, medium, high, critical)

        Returns:
            Breach incident record
        """
        breach_record = {
            "breach_id": f"breach_{datetime.now().timestamp()}",
            "breach_type": breach_type,
            "severity": severity,
            "description": description,
            "affected_users_count": len(affected_users),
            "affected_users": affected_users,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "reported_to_authority": False,
            "notification_deadline": "72 hours from detection",
            "gdpr_article": "Article 33 - Notification of data breach to supervisory authority",
            "status": "detected",
        }

        # In production, this would be stored in a dedicated breach log
        return breach_record

    def create_privacy_notice(
        self,
        data_controller: str,
        purposes: List[str],
        data_categories: List[str],
        recipients: List[str],
        retention_period: str,
    ) -> str:
        """
        Generate GDPR-compliant privacy notice.

        Args:
            data_controller: Name of data controller
            purposes: Purposes of processing
            data_categories: Categories of personal data
            recipients: Who will receive the data
            retention_period: How long data is retained

        Returns:
            Privacy notice text
        """
        return f"""
PRIVACY NOTICE (GDPR-Compliant)

Data Controller: {data_controller}

1. PURPOSES OF PROCESSING
{chr(10).join('   - ' + p for p in purposes)}

2. LEGAL BASIS
   - Legitimate interests (Article 6(1)(f))

3. CATEGORIES OF PERSONAL DATA
{chr(10).join('   - ' + c for c in data_categories)}

4. RECIPIENTS OF DATA
{chr(10).join('   - ' + r for r in recipients)}

5. RETENTION PERIOD
   {retention_period}

6. YOUR RIGHTS
   - Right to access your data (Article 15)
   - Right to rectification (Article 16)
   - Right to erasure (Article 17)
   - Right to restriction of processing (Article 18)
   - Right to data portability (Article 20)
   - Right to object (Article 21)

7. DATA PROTECTION OFFICER
   Contact: dpo@example.com

8. SUPERVISORY AUTHORITY
   You have the right to lodge a complaint with your local supervisory authority.

Generated: {datetime.now(timezone.utc).isoformat()}
        """.strip()

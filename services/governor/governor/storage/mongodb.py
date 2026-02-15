"""MongoDB storage backend for production use."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
except ImportError:
    raise ImportError(
        "MongoDB storage requires 'motor' package. "
        "Install with: pip install governor[mongodb]"
    )

from governor.core.context import ExecutionContext, ExecutionStatus
from governor.core.state import StateSnapshot
from governor.events.base import Event, EventType
from governor.storage.base import StorageBackend


class MongoDBStorage(StorageBackend):
    """
    MongoDB storage backend for production deployments.

    Provides persistent storage for execution contexts, state snapshots,
    events, and approval decisions.
    """

    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017",
        database_name: str = "governor",
    ):
        """
        Initialize MongoDB storage.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(connection_string)
        self.db: AsyncIOMotorDatabase = self.client[database_name]

        # Collections
        self.executions = self.db.executions
        self.snapshots = self.db.snapshots
        self.events = self.db.events
        self.approvals = self.db.approvals

    async def ensure_indexes(self) -> None:
        """Create indexes for optimal query performance."""
        # Execution indexes
        await self.executions.create_index("execution_id", unique=True)
        await self.executions.create_index("function_name")
        await self.executions.create_index("status")
        await self.executions.create_index("started_at")

        # Snapshot indexes
        await self.snapshots.create_index("snapshot_id", unique=True)
        await self.snapshots.create_index("execution_id")
        await self.snapshots.create_index("checkpoint")

        # Event indexes
        await self.events.create_index("event_id", unique=True)
        await self.events.create_index("execution_id")
        await self.events.create_index("event_type")
        await self.events.create_index("timestamp")

        # Approval indexes
        await self.approvals.create_index("execution_id", unique=True)

    async def store_execution(self, context: ExecutionContext) -> None:
        """Store or update an execution context."""
        await self.executions.update_one(
            {"execution_id": context.execution_id},
            {"$set": context.to_dict()},
            upsert=True,
        )

    async def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Retrieve an execution context by ID."""
        doc = await self.executions.find_one({"execution_id": execution_id})
        if doc:
            doc.pop("_id", None)  # Remove MongoDB _id
            return ExecutionContext(**doc)
        return None

    async def list_executions(
        self,
        function_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ExecutionContext]:
        """List execution contexts with optional filtering."""
        query: Dict[str, Any] = {}

        if function_name:
            query["function_name"] = function_name
        if status:
            query["status"] = status

        cursor = (
            self.executions.find(query)
            .sort("started_at", -1)
            .skip(offset)
            .limit(limit)
        )

        executions = []
        async for doc in cursor:
            doc.pop("_id", None)
            executions.append(ExecutionContext(**doc))

        return executions

    async def store_snapshot(self, snapshot: StateSnapshot) -> None:
        """Store a state snapshot."""
        await self.snapshots.update_one(
            {"snapshot_id": snapshot.snapshot_id},
            {"$set": snapshot.to_dict()},
            upsert=True,
        )

    async def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Retrieve a state snapshot by ID."""
        doc = await self.snapshots.find_one({"snapshot_id": snapshot_id})
        if doc:
            doc.pop("_id", None)
            return StateSnapshot(**doc)
        return None

    async def get_snapshots_by_execution(self, execution_id: str) -> List[StateSnapshot]:
        """Get all snapshots for an execution."""
        cursor = self.snapshots.find({"execution_id": execution_id}).sort(
            "captured_at", 1
        )

        snapshots = []
        async for doc in cursor:
            doc.pop("_id", None)
            snapshots.append(StateSnapshot(**doc))

        return snapshots

    async def store_event(self, event: Event) -> None:
        """Store an event."""
        await self.events.insert_one(event.to_dict())

    async def get_events(
        self,
        execution_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """Get events with optional filtering."""
        query: Dict[str, Any] = {}

        if execution_id:
            query["execution_id"] = execution_id
        if event_type:
            query["event_type"] = event_type

        cursor = (
            self.events.find(query)
            .sort("timestamp", -1)
            .skip(offset)
            .limit(limit)
        )

        events = []
        async for doc in cursor:
            doc.pop("_id", None)
            events.append(Event(**doc))

        return events

    async def store_approval(
        self,
        execution_id: str,
        approver: str,
        approved: bool,
        reason: Optional[str] = None,
    ) -> None:
        """Store an approval decision."""
        approval_data = {
            "execution_id": execution_id,
            "approver": approver,
            "approved": approved,
            "reason": reason,
            "decided_at": datetime.utcnow().isoformat(),
        }

        await self.approvals.update_one(
            {"execution_id": execution_id},
            {"$set": approval_data},
            upsert=True,
        )

    async def get_approval(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get approval decision for an execution."""
        doc = await self.approvals.find_one({"execution_id": execution_id})
        if doc:
            doc.pop("_id", None)
            return doc
        return None

    async def close(self) -> None:
        """Close MongoDB connection."""
        self.client.close()

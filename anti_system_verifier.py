import hashlib
import json
import time
from typing import Dict, Any, List, Tuple

class AntiSystemEngine:
    """
    Enforces deterministic state validation and strict cycle boundaries,
    rejecting unauthorized memory mutations or background drift.
    """
    def __init__(self, process_id: str, cycle_limit: int):
        self.process_id: str = process_id
        self.cycle_limit: int = cycle_limit
        self.ledger: List[Dict[str, Any]] = []

    def _canonical_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def calculate_holographic_root(self, log_stream: List[Dict[str, Any]]) -> str:
        state_hasher = hashlib.sha256()
        for entry in log_stream:
            entry_hash = self._canonical_hash(entry)
            state_hasher.update(entry_hash.encode('utf-8'))
        return state_hasher.hexdigest()

    def process_message(
        self,
        message: Dict[str, Any],
        claimed_root: str,
        cycles_consumed: int
    ) -> Tuple[bool, Dict[str, Any]]:
        ts = int(time.time())

        if cycles_consumed > self.cycle_limit:
            return False, {
                "process_id": self.process_id,
                "status": "HALT_CYCLE_EXCEEDED",
                "cycles_used": cycles_consumed,
                "cycle_limit": self.cycle_limit,
                "timestamp": ts
            }

        projected_logs = self.ledger + [message]
        expected_root = self.calculate_holographic_root(projected_logs)

        if expected_root != claimed_root:
            return False, {
                "process_id": self.process_id,
                "status": "DIVERGENCE_HALT",
                "expected_root": expected_root,
                "claimed_root": claimed_root,
                "timestamp": ts
            }

        self.ledger.append(message)
        return True, {
            "process_id": self.process_id,
            "status": "STATE_VERIFIED",
            "current_root": expected_root,
            "cycles_used": cycles_consumed,
            "timestamp": ts
        }

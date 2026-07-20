import hashlib
import json
import time
from typing import Dict, Any, List, Tuple

class AntiSystemKernel:
    """
    CRA Kernel Module
    Deterministic state engine enforcing:
    - canonical hashing
    - holographic replay
    - cycle-budget enforcement
    - divergence detection
    """

    def __init__(self, process_id: str, cycle_limit: int):
        self.process_id: str = process_id
        self.cycle_limit: int = cycle_limit
        self.ledger: List[Dict[str, Any]] = []

    def canonical_hash(self, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def holographic_root(self, log_stream: List[Dict[str, Any]]) -> str:
        state_hasher = hashlib.sha256()
        for entry in log_stream:
            entry_hash = self.canonical_hash(entry)
            state_hasher.update(entry_hash.encode("utf-8"))
        return state_hasher.hexdigest()

    def process(self, message: Dict[str, Any], claimed_root: str, cycles_used: int) -> Tuple[bool, Dict[str, Any]]:
        ts = int(time.time())

        if cycles_used > self.cycle_limit:
            return False, {
                "process_id": self.process_id,
                "status": "HALT_CYCLE_EXCEEDED",
                "cycles_used": cycles_used,
                "cycle_limit": self.cycle_limit,
                "timestamp": ts
            }

        projected = self.ledger + [message]
        expected_root = self.holographic_root(projected)

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
            "cycles_used": cycles_used,
            "timestamp": ts
        }

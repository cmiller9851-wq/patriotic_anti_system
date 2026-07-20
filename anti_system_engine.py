import hashlib
import json
from typing import Dict, Any, List, Tuple, Optional

class AntiSystemEngine:
    """
    Unified CRA Engine v2
    Optimized deterministic state engine enforcing:
    - O(1) state transitions via running root state
    - O(N) cold holographic replay recovery
    - Absolute determinism (no local host clock dependencies)
    - Cycle-budget enforcement
    - Immutable ledger progression
    """

    def __init__(self, process_id: str, cycle_limit: int):
        self.process_id: str = process_id
        self.cycle_limit: int = cycle_limit
        self.ledger: List[Dict[str, Any]] = []
        self._current_hasher: hashlib._Hash = hashlib.sha256()

    def canonical_hash(self, data: Dict[str, Any]) -> str:
        """
        Produces a canonical SHA-256 digest by sorting JSON keys
        and eliminating whitespace separators.
        """
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_current_root(self) -> str:
        """
        Returns the current accumulated state hash without mutating internal state.
        """
        return self._current_hasher.hexdigest()

    def calculate_projected_root(self, message: Dict[str, Any]) -> str:
        """
        Calculates the exact holographic state root if 'message' is appended.
        Operates in O(1) time complexity using clone().
        """
        hasher_clone = self._current_hasher.copy()
        msg_hash = self.canonical_hash(message)
        hasher_clone.update(msg_hash.encode("utf-8"))
        return hasher_clone.hexdigest()

    def holographic_replay(self, log_stream: List[Dict[str, Any]]) -> str:
        """
        Cold replay mechanism to re-evaluate and rebuild state root from scratch.
        Executes in O(N) time across the full log stream.
        """
        rebuilt_hasher = hashlib.sha256()
        for entry in log_stream:
            entry_hash = self.canonical_hash(entry)
            rebuilt_hasher.update(entry_hash.encode("utf-8"))
        return rebuilt_hasher.hexdigest()

    def process(self, message: Dict[str, Any], claimed_root: str, cycles_used: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluates incoming state mutations in O(1) against cycle limits and claimed roots.
        """
        # Strictly extract timestamp from message context for determinism
        msg_ts: Optional[int] = message.get("timestamp")

        if cycles_used > self.cycle_limit:
            return False, {
                "process_id": self.process_id,
                "status": "HALT_CYCLE_EXCEEDED",
                "cycles_used": cycles_used,
                "cycle_limit": self.cycle_limit,
                "timestamp": msg_ts
            }

        expected_root = self.calculate_projected_root(message)

        if expected_root != claimed_root:
            return False, {
                "process_id": self.process_id,
                "status": "DIVERGENCE_HALT",
                "expected_root": expected_root,
                "claimed_root": claimed_root,
                "timestamp": msg_ts
            }

        # Commit state update
        msg_hash = self.canonical_hash(message)
        self._current_hasher.update(msg_hash.encode("utf-8"))
        self.ledger.append(message)

        return True, {
            "process_id": self.process_id,
            "status": "STATE_VERIFIED",
            "current_root": expected_root,
            "cycles_used": cycles_used,
            "timestamp": msg_ts
        }


if __name__ == "__main__":
    engine = AntiSystemEngine(process_id="PROCESS_001", cycle_limit=1000)

    # Message 1
    msg_1 = {"action": "TRANSFER", "amount": 100, "target": "CU_882", "timestamp": 1700000000}
    claimed_root_1 = engine.calculate_projected_root(msg_1)

    success_1, res_1 = engine.process(msg_1, claimed_root_1, cycles_used=120)
    assert success_1 is True
    assert res_1["status"] == "STATE_VERIFIED"
    assert res_1["current_root"] == engine.get_current_root()

    # Message 2
    msg_2 = {"action": "STAKE", "amount": 500, "target": "CU_901", "timestamp": 1700000005}
    claimed_root_2 = engine.calculate_projected_root(msg_2)

    success_2, res_2 = engine.process(msg_2, claimed_root_2, cycles_used=210)
    assert success_2 is True

    # Verify Holographic Cold Replay Match
    replay_root = engine.holographic_replay(engine.ledger)
    assert replay_root == engine.get_current_root()

    print("AntiSystemEngine v2: O(1) Optimization and Replay Tests Passed.")

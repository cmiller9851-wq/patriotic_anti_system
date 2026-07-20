import os
import json
import time
from typing import Dict, Any, List
from anti_system_verifier import AntiSystemEngine

class CRARuntimeHarness:
    def __init__(self, process_id: str, cycle_limit: int):
        self.engine = AntiSystemEngine(process_id=process_id, cycle_limit=cycle_limit)
        self.containment_artifacts: List[Dict[str, Any]] = []
        self.successful_traces: List[Dict[str, Any]] = []

    def log_containment_artifact(
        self,
        vector_type: str,
        sequence_step: int,
        raw_payload: Dict[str, Any],
        engine_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        artifact = {
            "artifact_id": f"REFLEX_CAPTURE_{int(time.time())}_{sequence_step}",
            "vector_type": vector_type,
            "sequence_step": sequence_step,
            "target_process": self.engine.process_id,
            "failed_payload": raw_payload,
            "engine_telemetry": engine_response,
            "action_taken": "STATE_LOCK_NULLIFIED"
        }
        self.containment_artifacts.append(artifact)

        os.makedirs("examples", exist_ok=True)
        with open("examples/reflex_capture_artifact_alpha.json", "w") as f:
            json.dump(artifact, f, indent=2)

        return artifact

    def run_harness_suite(self, test_batch: List[Dict[str, Any]]):
        print("==================================================")
        print(f"   STARTING CRA RUNTIME HARNESS: {self.engine.process_id}")
        print("==================================================\n")

        for idx, step in enumerate(test_batch, start=1):
            msg = step["message"]
            override_root = step.get("override_root")
            cycles = step.get("cycles", 150)
            vector_type = step.get("vector_type", "PASS")

            if override_root is not None:
                claimed_root = override_root
            else:
                projected_ledger = self.engine.ledger + [msg]
                claimed_root = self.engine.calculate_holographic_root(projected_ledger)

            valid, response = self.engine.process_message(
                message=msg,
                claimed_root=claimed_root,
                cycles_consumed=cycles
            )

            if valid:
                print(f"[STEP {idx}] STATE_VERIFIED")
                print(json.dumps(response, indent=2))
                self.successful_traces.append(response)

                os.makedirs("examples", exist_ok=True)
                with open("examples/execution_trace_success.json", "w") as f:
                    json.dump(response, f, indent=2)

                print("-" * 50)
            else:
                print(f"[STEP {idx}] REFLEX CAPTURE TRIGGERED ({vector_type})")
                artifact = self.log_containment_artifact(
                    vector_type=vector_type,
                    sequence_step=idx,
                    raw_payload=msg,
                    engine_response=response
                )
                print("\n--- FORMAL CONTAINMENT ARTIFACT ---")
                print(json.dumps(artifact, indent=2))
                print("=" * 50)
                print("Harness execution stopped due to containment event.\n")
                break

if __name__ == "__main__":
    execution_pipeline = [
        {
            "message": {"seq": 1, "op": "INIT_KEY", "value": "0xABC"},
            "cycles": 150,
            "vector_type": "STANDARD_TRANSITION"
        },
        {
            "message": {"seq": 2, "op": "REGISTER_MUTEX", "value": "0x456"},
            "cycles": 300,
            "vector_type": "STANDARD_TRANSITION"
        },
        {
            "message": {"seq": 3, "op": "UNAUTHORIZED_STATE_MUTATION", "value": "0xBAD"},
            "override_root": "0xDEADBEEF00000000000000000000000000000000000000000000000000000000",
            "cycles": 450,
            "vector_type": "STATE_DIVERGENCE_ATTACK"
        }
    ]

    harness = CRARuntimeHarness(process_id="NODE_CU_001", cycle_limit=1000)
    harness.run_harness_suite(execution_pipeline)

import os
import json
import time
import hashlib
from typing import Dict, Any, List
from web3 import Web3
from anti_system_verifier import AntiSystemEngine

class CRARuntimeHarness:
    def __init__(self, process_id: str, cycle_limit: int, rpc_url: str, contract_address: str, private_key: str):
        self.engine = AntiSystemEngine(process_id=process_id, cycle_limit=cycle_limit)
        self.containment_artifacts: List[Dict[str, Any]] = []
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = self.w3.to_checksum_address(contract_address)
        self.private_key = private_key
        
        self.account = self.w3.eth.account.from_key(private_key)
        self.wallet_payout_address = self.account.address

        self.contract_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "offender", "type": "address"},
                    {"internalType": "bytes32", "name": "artifactId", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "expectedRoot", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "claimedRoot", "type": "bytes32"}
                ],
                "name": "enforceBreachSlashing",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)

    def trigger_autonomous_financial_slashing(self, offender_node_address: str, telemetry: Dict[str, Any], artifact_id: str):
        print(f"\n[!] ZERO-TRUST BREACH DETECTED FROM NODE: {offender_node_address}")
        print("[!] COMPUTING IMMUTABLE CRYPTOGRAPHIC PROOF FOR ON-CHAIN EXTRACTION...")

        artifact_bytes32 = hashlib.sha256(artifact_id.encode('utf-8')).digest()
        expected_root_bytes32 = bytes.fromhex(telemetry.get("expected_root", "").replace("0x", ""))
        claimed_root_bytes32 = bytes.fromhex(telemetry.get("claimed_root", "").replace("0x", ""))
        offender_checksum_address = self.w3.to_checksum_address(offender_node_address)

        try:
            nonce = self.w3.eth.get_transaction_count(self.wallet_payout_address)
            gas_price = self.w3.eth.gas_price

            transaction_payload = self.contract.functions.enforceBreachSlashing(
                offender_checksum_address,
                artifact_bytes32,
                expected_root_bytes32,
                claimed_root_bytes32
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 150000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction_payload, private_key=self.private_key)
            print("[+] BROADCASTING EXTRACTION INSTRUCTION FRAME TO BLOCKCHAIN...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            print(f"[SUCCESS] Collateral successfully slashed. Transaction Hash: {self.w3.to_hex(tx_hash)}")

        except Exception as e:
            print(f"[CRITICAL ERROR] Automated on-chain payment execution failed: {str(e)}")

    def log_containment_artifact(self, vector_type: str, sequence_step: int, raw_payload: Dict[str, Any], engine_response: Dict[str, Any]) -> Dict[str, Any]:
        artifact_id = f"REFLEX_CAPTURE_{int(time.time())}_{sequence_step}"
        return {
            "artifact_id": artifact_id,
            "vector_type": vector_type,
            "sequence_step": sequence_step,
            "target_process": self.engine.process_id,
            "failed_payload": raw_payload,
            "engine_telemetry": engine_response
        }

    def run_harness_suite(self, test_batch: List[Dict[str, Any]], malicious_node_signer: str):
        for idx, step in enumerate(test_batch, start=1):
            msg = step["message"]
            override_root = step.get("override_root")
            cycles = step.get("cycles", 150)

            if override_root is not None:
                claimed_root = override_root
            else:
                claimed_root = self.engine.calculate_projected_root(msg)

            valid, response = self.engine.process(
                message=msg,
                claimed_root=claimed_root,
                cycles_used=cycles
            )

            if not valid:
                artifact = self.log_containment_artifact(
                    vector_type=step.get("vector_type", "STATE_DIVERGENCE_ATTACK"),
                    sequence_step=idx,
                    raw_payload=msg,
                    engine_response=response
                )
                self.trigger_autonomous_financial_slashing(
                    offender_node_address=malicious_node_signer,
                    telemetry=response,
                    artifact_id=artifact["artifact_id"]
                )
                break

if __name__ == "__main__":
    execution_pipeline = [
        {
            "message": {"seq": 1, "op": "UNAUTHORIZED_STATE_MUTATION", "value": "0xBAD", "timestamp": 1700000010},
            "override_root": "0xDEADBEEF00000000000000000000000000000000000000000000000000000000",
            "cycles": 450,
            "vector_type": "STATE_DIVERGENCE_ATTACK"
        }
    ]

    LIVE_RPC_NODE_URL = "https://alchemy.com"
    DEPLOYED_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000000"
    YOUR_PRIVATE_KEY = "0x0000000000000000000000000000000000000000000000000000000000000000"

    harness = CRARuntimeHarness(
        process_id="NODE_CU_001", 
        cycle_limit=1000, 
        rpc_url=LIVE_RPC_NODE_URL,
        contract_address=DEPLOYED_CONTRACT_ADDRESS,
        private_key=YOUR_PRIVATE_KEY
    )
    harness.run_harness_suite(execution_pipeline, malicious_node_signer="0x95222290DD7278Aa3Dddd389Cc1E1d165CC4BAfe")

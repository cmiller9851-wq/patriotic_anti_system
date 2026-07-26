use sha2::{Sha256, Digest};
use std::collections::HashSet;

pub struct ControlFlowVector {
    allowed_hashes: HashSet<[u8; 32]>,
}

impl ControlFlowVector {
    pub fn new() -> Self {
        Self { allowed_hashes: HashSet::new() }
    }

    /// Registers a validated, mathematically secure instruction sequence into the sandbox baseline.
    pub fn register_allowed_block(&mut self, instructions: &[u8]) {
        let mut hasher = Sha256::new();
        hasher.update(instructions);
        let result = hasher.finalize();
        self.allowed_hashes.insert(result.into());
    }

    /// CRA-Grade Containment Vector validation layer. 
    /// Enforces absolute validation boundaries on inputs prior to state transition.
    pub fn verify_execution_safety(&self, instructions: &[u8]) -> Result<(), &'static str> {
        let mut hasher = Sha256::new();
        hasher.update(instructions);
        let result: [u8; 32] = hasher.finalize().into();

        if self.allowed_hashes.contains(&result) {
            Ok(())
        } else {
            Err("CRA Containment Boundary Fault: Untrusted execution vectors or altered layout detected.")
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cra_vector_enforcement() {
        let mut cfv = ControlFlowVector::new();
        let safe_payload = b"xor rax, rax; ret;";
        let unsafe_payload = b"mov rax, 0x3b; syscall;";

        cfv.register_allowed_block(safe_payload);
        assert!(cfv.verify_execution_safety(safe_payload).is_ok());
        assert!(cfv.verify_execution_safety(unsafe_payload).is_err());
    }
}

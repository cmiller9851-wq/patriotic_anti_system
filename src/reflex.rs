use serde::{Serialize, Deserialize};
use crate::replay::VirtualRegisterState;

#[derive(Serialize, Deserialize, Debug, PartialEq)]
pub struct ReflexCapture {
    pub timestamp_epoch_ns: u64,
    pub cycle_marker: u64,
    pub captured_state: VirtualRegisterState,
    pub cryptographic_signature: Vec<u8>,
}

impl ReflexCapture {
    pub fn serialize_artifact(&self) -> Result<Vec<u8>, bincode::Error> {
        bincode::serialize(self)
    }

    pub fn deserialize_artifact(bytes: &[u8]) -> Result<Self, bincode::Error> {
        bincode::deserialize(bytes)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_artifact_serialization_cycle() {
        let initial_state = VirtualRegisterState {
            rip: 0x1000,
            rax: 42,
            rbx: 7,
            memory_root_hash: [0u8; 32],
        };
        let capture = ReflexCapture {
            timestamp_epoch_ns: 1711843200000,
            cycle_marker: 88,
            captured_state: initial_state,
            cryptographic_signature: vec![0xAA, 0xBB, 0xCC],
        };

        let encoded = capture.serialize_artifact().unwrap();
        let decoded: ReflexCapture = ReflexCapture::deserialize_artifact(&encoded).unwrap();
        assert_eq!(capture, decoded);
    }
}

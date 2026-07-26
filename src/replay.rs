use serde::{Serialize, Deserialize};

#[derive(Clone, Serialize, Deserialize, Debug, PartialEq)]
pub struct VirtualRegisterState {
    pub rip: u64,
    pub rax: u64,
    pub rbx: u64,
    pub memory_root_hash: [u8; 32],
}

pub struct HolographicEngine {
    state_history: Vec<VirtualRegisterState>,
}

impl HolographicEngine {
    pub fn new(initial_state: VirtualRegisterState) -> Self {
        Self { state_history: vec![initial_state] }
    }

    pub fn commit_state(&mut self, state: VirtualRegisterState) {
        self.state_history.push(state);
    }

    /// Seamlessly shifts the system state backwards to a specific time horizon index.
    pub fn replay_to_tick(&self, tick: usize) -> Result<VirtualRegisterState, &'static str> {
        if tick >= self.state_history.len() {
            return Err("Holographic Horizon Error: Target state slice index does not exist.");
        }
        Ok(self.state_history[tick].clone())
    }
}

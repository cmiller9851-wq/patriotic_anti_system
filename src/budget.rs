pub struct CycleAccountant {
    max_budget: u64,
    consumed_cycles: u64,
}

impl CycleAccountant {
    pub fn new(max_budget: u64) -> Self {
        Self { max_budget, consumed_cycles: 0 }
    }

    /// Deducts execution units directly linked to incoming runtime requests.
    /// Halts processing instantly if the structural boundaries are crossed.
    pub fn consume(&mut self, cycles: u64) -> Result<(), &'static str> {
        if self.consumed_cycles.checked_add(cycles).map_or(true, |sum| sum > self.max_budget) {
            return Err("Cycle Budget Exhausted: Execution terminated to preserve determinism.");
        }
        self.consumed_cycles += cycles;
        Ok(())
    }

    pub fn total_consumed(&self) -> u64 {
        self.consumed_cycles
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_strict_cycle_accounting() {
        let mut accountant = CycleAccountant::new(100);
        assert!(accountant.consume(40).is_ok());
        assert_eq!(accountant.total_consumed(), 40);
        assert!(accountant.consume(61).is_err());
    }
}

from deephyper.hpo import CBO
from datetime import datetime, timezone

class ConstraintAwareCBO(CBO):
    def __init__(self, *args, is_valid_config=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_valid_config = is_valid_config

    def ask(self, n=1):
        valid = []
        attempts = 0
        max_attempts = 100
        total_candidates = 0

        while len(valid) < n and attempts < max_attempts:
            # Over-sample to increase chances of valid configs
            batch_size = max(n * 2, 10)
            candidates = super().ask(batch_size)
            total_candidates += len(candidates)

            for cand in candidates:
                if not isinstance(cand, dict):
                    continue
                if self.is_valid_config and self.is_valid_config(cand):
                    valid.append(cand)
                if len(valid) >= n:
                    break
            attempts += 1

        if len(valid) < n:
            raise RuntimeError(f"ConstraintAwareCBO: Only {len(valid)} valid configs found after {attempts} attempts.")

        print(f"🔎 ConstraintAwareCBO: Found {len(valid)} valid configs after evaluating {total_candidates} candidates in {attempts} attempts.")

        # Save cumulative stats
        if not hasattr(self, "ask_log"):
            self.ask_log = []

        self.ask_log.append({
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            "n_valid": len(valid),
            "n_asked": total_candidates,
            "attempts": attempts
        })

        return valid[:n]

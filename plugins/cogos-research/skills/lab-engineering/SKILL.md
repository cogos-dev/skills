---
name: lab-engineering
description: Lab execution protocols for computational experiments - environment verification, defensive coding, checkpointing, and reproducibility. Use when running experiments, validating environments, or ensuring results are reproducible.
---

# Lab Engineering Skill

Protocols for reliable experiment execution in computational environments.

## Environment Verification Protocol

Before running any experiment:

1. **Check runtime versions**
   ```bash
   python3 --version
   pip list | grep -E "numpy|scipy|matplotlib|pandas"
   ```

2. **Verify resource constraints**
   ```bash
   # Memory available
   python3 -c "import os; print(f'Memory: {os.sysconf(\"SC_PAGE_SIZE\") * os.sysconf(\"SC_PHYS_PAGES\") / (1024**3):.1f} GB')"

   # Disk space
   df -h .
   ```

3. **Test write access**
   ```bash
   touch /tmp/test-write && rm /tmp/test-write
   ```

4. **Document environment** in lab notebook before proceeding.

## Defensive Coding Patterns

### Checkpointing

```python
import json
from pathlib import Path
from datetime import datetime

def checkpoint(data, name, step):
    """Save intermediate results with metadata."""
    path = Path(f"checkpoints/{name}_step{step}.json")
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "data": data
    }

    with open(path, 'w') as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"Checkpoint saved: {path}")
    return path
```

### Progress Logging

```python
import sys

def log_progress(current, total, message=""):
    """Print progress without newline spam."""
    pct = current / total * 100
    sys.stdout.write(f"\r[{pct:5.1f}%] {message}")
    sys.stdout.flush()
    if current == total:
        print()  # Final newline
```

### Error Recovery

```python
import time

def with_retry(fn, max_attempts=3, delay=1.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            time.sleep(delay * (2 ** attempt))
```

### Safe File Operations

```python
from pathlib import Path
import shutil

def safe_write(path, content, backup=True):
    """Write file with optional backup of existing."""
    path = Path(path)

    if path.exists() and backup:
        backup_path = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, backup_path)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path
```

## Lab Notebook Format

Create at session start:

```markdown
# Lab Notebook: {experiment-name}
Date: {YYYY-MM-DD}
Operator: {name}

## Environment
- Python: {version}
- Key packages: {list}
- Memory: {X} GB available
- Disk: {Y} GB free

## Objectives
- [ ] {objective 1}
- [ ] {objective 2}

## Session Log

### {HH:MM} - Start
{Initial observations}

### {HH:MM} - {Step description}
Command: `{command}`
Result: {outcome}
Notes: {observations}

## Results
{Summary of outputs}

## Discoveries
{Environment quirks, unexpected behaviors}
```

## Reproducibility Checklist

Before declaring an experiment complete:

- [ ] All random seeds recorded
- [ ] Environment versions documented
- [ ] Input data checksummed
- [ ] Output data saved with metadata
- [ ] Steps documented in lab notebook
- [ ] Results can be reproduced from notebook alone

## Environment Profiles

Track environment capabilities:

```python
import platform
import sys

def get_env_profile():
    """Generate environment fingerprint."""
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "hostname": platform.node(),
    }
```

## Memory Management

For long-running experiments:

```python
import gc

def clear_memory():
    """Force garbage collection and report."""
    collected = gc.collect()
    print(f"Garbage collector freed {collected} objects")
```

## Session Boundaries

Start of session:
1. Load environment profile
2. Verify dependencies
3. Create lab notebook
4. Note any changes from last session

End of session:
1. Checkpoint all state
2. Complete lab notebook
3. Note discoveries for next session

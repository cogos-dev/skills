---
name: experiment-design
description: Design rigorous experiments with clear hypotheses, controls, metrics, and analysis plans. Covers A/B testing, ablation studies, benchmarking, and proof-of-concept validation. Use when planning experiments to test technical hypotheses or compare approaches.
---

# Experiment Design Skill

Protocols for rigorous computational experimentation.

## Experiment Structure

### Core Components

Every experiment needs:

1. **Hypothesis** - What we're testing
2. **Null hypothesis** - What we expect if there's no effect
3. **Variables** - What we're varying and what we're measuring
4. **Controls** - What we're holding constant
5. **Success criteria** - How we'll know if hypothesis is supported

### Template

```python
"""
Experiment: {name}

Hypothesis: {specific claim being tested}
Null Hypothesis: {what we expect if effect is absent}

Independent Variables:
  - {var1}: {range/values}
  - {var2}: {range/values}

Dependent Variables (Metrics):
  - {metric1}: {what it measures}
  - {metric2}: {what it measures}

Controls:
  - {held constant 1}
  - {held constant 2}

Trials: {N} independent runs per condition
Random Seed: {seed or seeding strategy}

Success Criteria:
  - {criterion 1}
  - {criterion 2}

Output Files:
  - {file1}: {description}
  - {file2}: {description}
"""
```

## Statistical Rigor

### Sample Sizes

Never draw conclusions from single runs.

| Situation | Minimum Trials | Reasoning |
|-----------|----------------|-----------|
| Noisy measurement | >= 30 | Central limit theorem |
| Rare events | >= 100 | Sufficient occurrence probability |
| Parameter sweep | >= 10 per point | Error bar estimation |
| Comparison | N such that power >= 0.8 | Detect expected effect size |

### Error Bars

Always report uncertainty:

```python
import numpy as np

def summarize(data):
    """Return mean and standard error."""
    mean = np.mean(data)
    std_err = np.std(data, ddof=1) / np.sqrt(len(data))
    return mean, std_err

# Report as: {mean} +/- {std_err}
```

### Confidence Intervals

```python
from scipy import stats

def confidence_interval(data, confidence=0.95):
    """Compute confidence interval for mean."""
    n = len(data)
    mean = np.mean(data)
    se = stats.sem(data)
    h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean - h, mean + h
```

## Parameter Sweeps

### Grid Search

```python
from itertools import product

def parameter_grid(param_ranges):
    """Generate all parameter combinations."""
    keys = param_ranges.keys()
    values = param_ranges.values()
    for combo in product(*values):
        yield dict(zip(keys, combo))

# Usage
params = {
    'alpha': [0.1, 0.5, 1.0],
    'beta': [0.01, 0.1],
    'n': [100, 1000]
}
for config in parameter_grid(params):
    run_experiment(config)
```

### Latin Hypercube Sampling

For high-dimensional parameter spaces:

```python
from scipy.stats import qmc

def latin_hypercube_sample(bounds, n_samples):
    """Sample parameter space efficiently."""
    d = len(bounds)
    sampler = qmc.LatinHypercube(d=d)
    sample = sampler.random(n=n_samples)

    # Scale to bounds
    l_bounds = [b[0] for b in bounds]
    u_bounds = [b[1] for b in bounds]
    return qmc.scale(sample, l_bounds, u_bounds)
```

## Controls and Baselines

### Types of Controls

| Control Type | Purpose | Example |
|--------------|---------|---------|
| Negative control | Verify null effect | Random data input |
| Positive control | Verify method works | Known-answer test case |
| Ablation | Isolate component effects | Remove one feature |
| Baseline | Comparison point | Simple/standard method |

### Ablation Studies

When testing system with multiple components:

```python
def ablation_study(full_system, components):
    """Test contribution of each component."""
    results = {'full': run(full_system)}

    for component in components:
        ablated = full_system.without(component)
        results[f'without_{component}'] = run(ablated)

    return results
```

## Reproducibility

### Random Seed Management

```python
import random
import numpy as np

def set_all_seeds(seed):
    """Set seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # Add framework-specific seeds as needed

def get_seed_sequence(base_seed, n_runs):
    """Generate independent seeds for multiple runs."""
    rng = np.random.default_rng(base_seed)
    return rng.integers(0, 2**31, size=n_runs)
```

### Experiment Logging

```python
import json
from datetime import datetime

def log_experiment(config, results, path):
    """Save experiment with full context."""
    record = {
        'timestamp': datetime.now().isoformat(),
        'config': config,
        'results': results,
        'environment': get_environment_info()
    }
    with open(path, 'w') as f:
        json.dump(record, f, indent=2, default=str)
```

## Visualization Standards

### Basic Plot Requirements

```python
import matplotlib.pyplot as plt

def standard_plot(x, y, yerr=None, xlabel='', ylabel='', title=''):
    """Create publication-quality plot."""
    fig, ax = plt.subplots(figsize=(8, 6))

    if yerr is not None:
        ax.errorbar(x, y, yerr=yerr, fmt='o-', capsize=3)
    else:
        ax.plot(x, y, 'o-')

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig, ax
```

### Multi-condition Comparison

```python
def comparison_plot(conditions, means, errors, labels):
    """Bar plot comparing conditions."""
    fig, ax = plt.subplots(figsize=(10, 6))

    x = range(len(conditions))
    ax.bar(x, means, yerr=errors, capsize=5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    plt.tight_layout()
    return fig, ax
```

## Result Interpretation

### What Can We Conclude?

| Evidence | Conclusion Strength |
|----------|---------------------|
| p < 0.05, large effect | Strong support |
| p < 0.05, small effect | Statistically significant, practical significance unclear |
| p > 0.05, small sample | Inconclusive - need more data |
| Consistent across conditions | Robust finding |
| Effect depends on parameters | Conditional relationship |

### Reporting Template

```markdown
## Results: {experiment name}

### Main Finding
{One sentence summary}

### Statistical Summary
- Effect size: {value} +/- {error}
- Significance: p = {value}
- Confidence interval: [{lower}, {upper}]

### Robustness
- Across {N} trials: {consistent/variable}
- Sensitivity to {parameter}: {high/low}

### Limitations
- {limitation 1}
- {limitation 2}

### Interpretation
{What this means, what it doesn't mean}
```

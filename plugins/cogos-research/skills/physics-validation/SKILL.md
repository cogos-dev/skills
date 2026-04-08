---
name: physics-validation
description: Protocols for validating physical plausibility of computational results - dimensional analysis, limiting cases, order-of-magnitude estimates, and analytical cross-checks. Use when checking if results make physical sense.
---

# Physics Validation Skill

Protocols for ensuring computational results are physically plausible.

## Dimensional Analysis

### The Fundamental Check

Every physical quantity has dimensions. Units must balance in any equation.

**Base dimensions (SI):**
- [L] Length (meters)
- [M] Mass (kilograms)
- [T] Time (seconds)
- [I] Current (amperes)
- [K] Temperature (kelvin)
- [N] Amount (moles)
- [J] Luminosity (candela)

### Dimensional Consistency

For any equation A = B:
- dim(A) must equal dim(B)
- Addition/subtraction requires matching dimensions
- Exponents must be dimensionless

```python
def check_dimensions(left_dims, right_dims):
    """Verify dimensional consistency."""
    if left_dims != right_dims:
        raise ValueError(f"Dimensional mismatch: {left_dims} vs {right_dims}")
    return True
```

### Common Derived Quantities

| Quantity | Dimensions | SI Units |
|----------|------------|----------|
| Velocity | [L][T]^-1 | m/s |
| Acceleration | [L][T]^-2 | m/s^2 |
| Force | [M][L][T]^-2 | N |
| Energy | [M][L]^2[T]^-2 | J |
| Power | [M][L]^2[T]^-3 | W |
| Entropy | [M][L]^2[T]^-2[K]^-1 | J/K |
| Information | dimensionless | bits/nats |

### Dimensional Traps

Watch for:
- Logarithm arguments must be dimensionless
- Exponential arguments must be dimensionless
- Trig function arguments must be dimensionless (radians)
- Dimensionless ratios are often the meaningful quantities

## Limiting Cases

### The Sanity Check

Before trusting a general result, check that it reduces correctly in limits:

1. **Weak coupling limit** - Does it reduce to non-interacting case?
2. **Strong coupling limit** - Does behavior saturate appropriately?
3. **Large/small parameter limits** - Asymptotic behavior correct?
4. **Classical limit** - Does quantum reduce to classical?
5. **Equilibrium limit** - Does dynamics reach expected steady state?

### Template

```markdown
## Limiting Case Analysis: {quantity}

### Case 1: {limit description}
When {parameter} -> {limit value}:
- Expected: {physical expectation}
- Observed: {what the model gives}
- Match: {yes/no, explanation}

### Case 2: {next limit}
...
```

## Order of Magnitude Estimates

### Before Detailed Calculation

Get the rough answer first. If detailed calculation differs by orders of magnitude, something is wrong.

### Fermi Estimation Approach

1. Identify relevant scales
2. Use dimensional analysis to constrain form
3. Estimate coefficients (often O(1))
4. Compare to detailed result

### Example Pattern

```markdown
## Order of Magnitude: {quantity}

Relevant scales:
- Length: {characteristic length} ~ {value}
- Time: {characteristic time} ~ {value}
- Energy: {characteristic energy} ~ {value}

Dimensional estimate: {quantity} ~ {scale combination}
Expected magnitude: ~ {power of 10}

Detailed result: {actual value}
Agreement: {within order of magnitude? If not, why?}
```

## Analytical Cross-Checks

### When to Use

- Verify numerics against solvable subcases
- Check conservation laws are satisfied
- Validate symmetry properties

### Conservation Laws

| Law | What is Conserved | How to Check |
|-----|-------------------|--------------|
| Energy | Total energy | Sum before = sum after |
| Momentum | Total momentum | Vector sum conserved |
| Probability | Total probability = 1 | Integral/sum = 1 |
| Information (closed) | von Neumann entropy | Check for spurious changes |

### Symmetry Properties

- Time-reversal: Is dynamics reversible when it should be?
- Spatial symmetry: Does solution respect boundary conditions?
- Exchange symmetry: Bosons/fermions behave correctly?

## Physical Plausibility Checklist

Before accepting any result:

- [ ] Dimensions are consistent
- [ ] Limiting cases work correctly
- [ ] Order of magnitude is reasonable
- [ ] Conservation laws satisfied
- [ ] No physically impossible values (negative probabilities, etc.)
- [ ] Behavior is continuous where it should be
- [ ] Singularities are physically meaningful

## Red Flags

Watch for these warning signs:

| Red Flag | Possible Issue |
|----------|----------------|
| Negative probability | Normalization error |
| Energy from nothing | Conservation violation |
| Faster-than-light | Causality violation |
| Infinite values | Missing regularization |
| Non-smooth where smooth expected | Numerical instability |
| Wrong limiting behavior | Formula error |

## Validation Template

```markdown
## Physics Validation: {result description}

### Dimensional Analysis
- Claimed dimensions: {X}
- Verified: {yes/no}

### Limiting Cases
1. {case 1}: {pass/fail}
2. {case 2}: {pass/fail}

### Order of Magnitude
- Estimate: {value}
- Result: {value}
- Agreement: {within factor of X}

### Conservation Laws
- {law 1}: {checked/violated}
- {law 2}: {checked/violated}

### Physical Plausibility
- [ ] All values in physical range
- [ ] No spurious singularities
- [ ] Behavior matches intuition

### Verdict
{VALID / NEEDS INVESTIGATION / INVALID}
{If not valid, what is wrong}
```

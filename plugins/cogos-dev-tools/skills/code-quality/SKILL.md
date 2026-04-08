---
name: code-quality
description: Protocols for writing maintainable code - clarity, testing, error handling, refactoring, and best practices. Use when implementing features, reviewing code, or improving existing code.
---

# Code Quality Skill

Protocols for writing code that works, reads well, and survives maintenance.

## Core Principles

### 1. Clarity Over Cleverness

Code is read more than written. If it's clever and confusing, it's just confusing.

```python
# Clever (bad)
result = [x for x in data if x and not any(x in s for s in excluded)]

# Clear (good)
result = []
for item in data:
    if item is None:
        continue
    if is_excluded(item, excluded):
        continue
    result.append(item)
```

### 2. Make It Work, Make It Right, Make It Fast

In that order. Don't optimize what doesn't work yet.

### 3. The Simplest Thing That Could Possibly Work

Start simple. Add complexity only when needed.

## Naming

### Variables

| Type | Convention | Example |
|------|------------|---------|
| Boolean | `is_`, `has_`, `can_` | `is_valid`, `has_error` |
| Count | `n_`, `num_`, `_count` | `n_items`, `error_count` |
| Collection | Plural | `users`, `items` |
| Single item | Singular | `user`, `item` |

### Functions

| Type | Convention | Example |
|------|------------|---------|
| Query | `get_`, `find_`, `is_` | `get_user()`, `is_valid()` |
| Action | Verb | `create_user()`, `send_email()` |
| Transformation | `to_`, `from_` | `to_json()`, `from_dict()` |

### Bad Names

Avoid:
- Single letters (except `i`, `j` in loops, `x`, `y` for coordinates)
- Abbreviations that aren't universal
- Generic names (`data`, `info`, `stuff`)
- Hungarian notation (`strName`, `arrItems`)

## Functions

### Good Functions

- Do one thing
- Fit on one screen (~25 lines)
- Have clear inputs and outputs
- Handle errors explicitly

```python
def calculate_total(items: list[Item], tax_rate: float) -> float:
    """Calculate total price including tax.

    Args:
        items: List of items with .price attribute
        tax_rate: Tax rate as decimal (e.g., 0.1 for 10%)

    Returns:
        Total price including tax

    Raises:
        ValueError: If tax_rate is negative
    """
    if tax_rate < 0:
        raise ValueError(f"Tax rate cannot be negative: {tax_rate}")

    subtotal = sum(item.price for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
```

### Function Smells

- Too many parameters (> 3-4)
- Boolean parameters (split into two functions)
- Side effects hidden in name that sounds like query
- Return value sometimes None with no indication

## Error Handling

### Be Explicit

```python
# Bad: silent failure
def get_user(user_id):
    try:
        return db.find(user_id)
    except:
        return None

# Good: explicit about failure modes
def get_user(user_id: int) -> User:
    """Fetch user by ID.

    Raises:
        UserNotFoundError: If user doesn't exist
        DatabaseError: If database is unavailable
    """
    try:
        user = db.find(user_id)
    except ConnectionError as e:
        raise DatabaseError(f"Database unavailable: {e}")

    if user is None:
        raise UserNotFoundError(f"No user with ID {user_id}")

    return user
```

### Error Handling Patterns

```python
# Fail fast
def process(data):
    if not data:
        raise ValueError("Data cannot be empty")
    # ... rest of function

# Use context managers for cleanup
with open(path) as f:
    data = f.read()
# File closed even if exception

# Specific exceptions
try:
    result = risky_operation()
except SpecificError as e:
    handle_specific_case(e)
except OtherError as e:
    handle_other_case(e)
# Never bare except:
```

## Testing

### What to Test

| Test Type | Purpose | Coverage |
|-----------|---------|----------|
| Unit | Single function/class | All public methods |
| Integration | Components together | Key interactions |
| Edge cases | Boundary conditions | Empty, large, negative |
| Error cases | Failure handling | All raise statements |

### Test Structure

```python
def test_calculate_total_with_tax():
    # Arrange
    items = [Item(price=10.0), Item(price=20.0)]
    tax_rate = 0.1

    # Act
    result = calculate_total(items, tax_rate)

    # Assert
    assert result == 33.0  # (10 + 20) * 1.1
```

### Good Test Properties

- **Fast** - Milliseconds, not seconds
- **Independent** - No order dependence
- **Repeatable** - Same result every time
- **Self-checking** - Pass/fail, no manual inspection
- **Timely** - Written close to code

## Refactoring

### When to Refactor

- Before adding feature (make room)
- After making it work (clean up)
- When you understand it better
- When tests are green

### Common Refactorings

| Smell | Refactoring |
|-------|-------------|
| Long function | Extract function |
| Duplicate code | Extract function/class |
| Long parameter list | Introduce parameter object |
| Primitive obsession | Introduce class |
| Feature envy | Move method |
| Shotgun surgery | Move related code together |

### Extract Function Example

```python
# Before
def process_order(order):
    # Validate
    if not order.items:
        raise ValueError("Empty order")
    if not order.customer:
        raise ValueError("No customer")
    if order.total < 0:
        raise ValueError("Negative total")

    # Process
    # ... 50 more lines

# After
def process_order(order):
    validate_order(order)
    # ... process

def validate_order(order):
    if not order.items:
        raise ValueError("Empty order")
    if not order.customer:
        raise ValueError("No customer")
    if order.total < 0:
        raise ValueError("Negative total")
```

## Code Review Checklist

### Correctness
- [ ] Does it work?
- [ ] Are edge cases handled?
- [ ] Are errors handled appropriately?

### Clarity
- [ ] Is the purpose obvious?
- [ ] Are names descriptive?
- [ ] Is it easy to follow?

### Maintainability
- [ ] Is it testable?
- [ ] Are there tests?
- [ ] Would future-you understand it?

### Performance
- [ ] Any obvious inefficiencies?
- [ ] Appropriate data structures?
- [ ] (Only if performance matters for this code)

## Debugging

### Systematic Approach

1. **Reproduce** - Make it fail consistently
2. **Isolate** - Find smallest failing case
3. **Inspect** - Print/log state at key points
4. **Hypothesize** - What could cause this?
5. **Test** - Verify your hypothesis
6. **Fix** - Make minimal change
7. **Verify** - Confirm fix, no regressions

### Debugging Prints

```python
def debug_state(name, value):
    """Print variable state for debugging."""
    print(f"DEBUG {name}: {value!r} (type: {type(value).__name__})")

# Usage
debug_state("items", items)
debug_state("total", total)
```

### Rubber Duck Debugging

Explain the problem out loud, line by line. The act of explanation often reveals the bug.

## Documentation

### What to Document

| Type | When | How |
|------|------|-----|
| Module | Complex module | Module-level docstring |
| Class | Public class | Class docstring |
| Function | Public function | Function docstring |
| Inline | Tricky code | Comment above |
| README | Project | Project root |

### Good vs Bad Comments

```python
# Bad: says what (obvious from code)
i += 1  # increment i

# Good: says why (not obvious)
i += 1  # Skip header row

# Bad: outdated
# Returns user or None  <- but now raises exception
def get_user(id): ...

# Good: kept in sync with code
def get_user(id) -> User:
    """Fetch user. Raises UserNotFoundError if missing."""
```

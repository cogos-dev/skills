---
name: systems-architecture
description: Protocols for designing reliable systems - failure mode analysis, operational concerns, scalability, and infrastructure patterns. Use when designing systems that need to survive production.
---

# Systems Architecture Skill

Protocols for designing systems that survive contact with reality.

## Failure Mode Analysis

### Everything Fails

The question is not *if* but *when* and *how gracefully*.

### Failure Categories

| Type | Examples | Mitigation |
|------|----------|------------|
| Network | Partition, latency, packet loss | Timeouts, retries, circuit breakers |
| Hardware | Disk, memory, CPU | Redundancy, replication |
| Software | Bugs, OOM, deadlock | Monitoring, auto-restart, limits |
| Human | Misconfiguration, accidents | Validation, rollback, review |
| External | Third-party outage, API changes | Fallbacks, caching, abstraction |

### Failure Analysis Template

```markdown
## Failure Mode Analysis: {component}

### Failure: {description}
**Probability:** {high/medium/low}
**Impact:** {severity}
**Detection:** {how we'll know}
**Response:** {what happens}
**Recovery:** {how we restore}

### Failure: {next failure}
...

### Blast Radius
{What's affected when this component fails}

### Mitigations
- {mitigation 1}
- {mitigation 2}
```

## Operational Concerns

### The Three Questions

For any system:
1. How do you deploy it?
2. How do you know it's healthy?
3. How do you roll back?

### Observability

| Type | Purpose | Examples |
|------|---------|----------|
| Metrics | Quantitative health | Latency, error rate, throughput |
| Logs | Event details | Request traces, errors |
| Traces | Request flow | Distributed call chains |

### Health Checks

```python
def health_check():
    """Return system health status."""
    checks = {
        'database': check_db_connection(),
        'cache': check_cache_connection(),
        'disk': check_disk_space(),
        'memory': check_memory_usage(),
    }

    all_healthy = all(checks.values())
    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks
    }
```

### Runbook Template

```markdown
## Runbook: {scenario}

### Symptoms
- {what you'll see}

### Diagnosis Steps
1. Check {X}: `{command}`
2. Check {Y}: `{command}`

### Resolution
1. {step 1}
2. {step 2}

### Escalation
If unresolved after {time}: contact {who}

### Post-Incident
- [ ] Root cause identified
- [ ] Fix deployed
- [ ] Monitoring updated
```

## Scalability

### Scaling Dimensions

| Dimension | Strategy | Considerations |
|-----------|----------|----------------|
| Load | Horizontal scaling | Statelessness, load balancing |
| Data | Sharding, partitioning | Consistency, hot spots |
| Users | Multi-tenancy | Isolation, fair sharing |
| Geography | Replication, CDN | Latency, consistency |

### Capacity Planning

Questions to answer:
- What's current usage?
- What's the growth rate?
- What's the ceiling of current architecture?
- When do we need to scale?

### Load Testing

```bash
# Example with wrk
wrk -t12 -c400 -d30s http://localhost:8080/api

# Key metrics
# - Requests/sec (throughput)
# - Latency distribution (p50, p95, p99)
# - Error rate under load
```

## Reliability Patterns

### Circuit Breaker

Prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.state = 'closed'  # closed, open, half-open
        self.last_failure = None

    def call(self, fn):
        if self.state == 'open':
            if time.time() - self.last_failure > self.timeout:
                self.state = 'half-open'
            else:
                raise CircuitOpenError()

        try:
            result = fn()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failures = 0
        self.state = 'closed'

    def on_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.state = 'open'
```

### Retry with Backoff

```python
def retry_with_backoff(fn, max_attempts=3, base_delay=1.0):
    """Retry with exponential backoff and jitter."""
    import random

    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise

            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0, delay * 0.1)
            time.sleep(delay + jitter)
```

### Bulkhead

Isolate failures:

```python
from concurrent.futures import ThreadPoolExecutor

class Bulkhead:
    """Limit concurrent calls to a resource."""

    def __init__(self, max_concurrent=10):
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def call(self, fn, timeout=30):
        future = self.executor.submit(fn)
        return future.result(timeout=timeout)
```

## Architecture Patterns

### Stateless Services

| Benefit | Implementation |
|---------|----------------|
| Easy scaling | No session affinity needed |
| Resilient | Any instance can serve any request |
| Simple deploys | No state migration |

Store state in:
- Databases (persistent)
- Caches (ephemeral, fast)
- Message queues (async processing)

### Event-Driven

```
Producer -> Message Queue -> Consumer(s)

Benefits:
- Decoupling
- Async processing
- Replay capability
- Load leveling
```

### CQRS (Command Query Responsibility Segregation)

```
Writes -> Command Model -> Event Store
                              |
                              v
                     Projections
                              |
Reads <- Query Model <--------
```

## System Design Template

```markdown
## System Design: {name}

### Requirements
**Functional:**
- {requirement 1}
- {requirement 2}

**Non-Functional:**
- Latency: {target}
- Throughput: {target}
- Availability: {target}

### Components
{Diagram or description of main components}

### Data Flow
{How data moves through the system}

### Failure Modes
{Key failure scenarios and mitigations}

### Scaling Strategy
{How this scales with load}

### Operational Concerns
- Deployment: {strategy}
- Monitoring: {what's tracked}
- Rollback: {procedure}

### Open Questions
- {question 1}
- {question 2}
```

## Architecture Review Checklist

Before deploying:

- [ ] Single points of failure identified and mitigated
- [ ] Failure modes documented
- [ ] Health checks implemented
- [ ] Metrics and logging in place
- [ ] Deployment procedure documented
- [ ] Rollback procedure tested
- [ ] Load testing completed
- [ ] Security review done
- [ ] Runbooks written
- [ ] On-call responsibilities assigned

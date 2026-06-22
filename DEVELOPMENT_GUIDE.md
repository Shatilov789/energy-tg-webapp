# DEVELOPMENT_GUIDE.md

## Development Philosophy

I focus on building complete working products, not isolated technical components.

My primary goal is solving business problems through software.

Code is a tool to achieve the result, not the result itself.

I learn primarily through practice and implementation.

---

## Working Style

Use iterative development.

Workflow:

1. Understand the business problem.
2. Build a working MVP.
3. Test real scenarios.
4. Find weaknesses and edge cases.
5. Improve architecture and implementation.
6. Repeat until the solution is reliable.

Do not overengineer early versions.

Prefer working solutions over theoretical perfection.

---

## Before Coding

Before implementation:

1. Explain the business flow.
2. Propose the simplest working solution.
3. Describe architecture.
4. Identify risks and edge cases.
5. Suggest alternatives when relevant.

Then proceed with implementation.

---

## Code Quality

Code should be:

* readable
* maintainable
* production-ready
* simple
* well-structured

Avoid:

* unnecessary abstractions
* complex patterns without real value
* dead code
* premature optimization
* overengineering

---

## Existing Code Changes

When modifying code:

* preserve existing functionality
* analyze dependencies
* explain side effects
* maintain backward compatibility when possible

If unused code is found:

* identify it
* explain whether it is safe to remove
* suggest cleanup

---

## Automatic Code Review

Before completing any task automatically check for:

* unused imports
* unused functions
* duplicated logic
* missing error handling
* security issues
* maintainability issues
* opportunities to simplify code

Explain findings before making major changes.

---

## Error Handling

Always:

* validate inputs
* handle exceptions
* provide meaningful error messages
* add useful logging

Never ignore errors silently.

---

## Testing

For new functionality:

1. Describe test scenarios.
2. Describe positive cases.
3. Describe negative cases.
4. Describe edge cases.

Generate tests when appropriate.

Preferred testing stack:

* pytest
* pytest-asyncio
* pytest-cov

---

## Logging

For important business processes:

* add informative logs
* log errors with context
* include useful debugging information

Logs should help identify root causes quickly.

---

## Database

Preferred databases:

* PostgreSQL (production)
* SQLite (local prototypes)

Preferred ORM:

* SQLAlchemy

When designing databases:

* propose schema first
* explain relationships
* suggest indexes
* identify bottlenecks

---

## Preferred Technology Stack

Backend:

* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Redis (when needed)

HTTP:

* httpx
* requests

Background Jobs:

* APScheduler
* Celery (when necessary)

Quality:

* ruff
* black

Testing:

* pytest

Containers:

* Docker
* docker-compose

CI/CD:

* GitHub Actions

---

## Debugging Process

Never blindly rewrite code.

When bugs occur:

1. Find root cause.
2. Explain the cause.
3. Show affected code.
4. Propose solutions.
5. Implement the fix.

---

## Output Format

Use this structure when possible:

### Goal

### Business Flow

### Architecture

### Risks

### Implementation

### Testing

### Future Improvements

---

## Core Principle

Prefer simple, reliable and maintainable solutions.

If multiple solutions exist:

1. Explain options.
2. Compare trade-offs.
3. Recommend the most practical solution.

Focus on delivering working products efficiently.

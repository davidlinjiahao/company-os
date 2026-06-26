---
name: eval
description: Universal evaluation framework for MCPs, Agents, and Skills. Also includes security auditing — "/eval secure" for OWASP code review + config scan. Run with "/eval [component]" or "/eval --list".
user-invocable: true
disable-model-invocation: false
argument-hint: "[component|secure] [--category X] [--verbose] [--save]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, AskUserQuestion
---

# Universal Eval Framework

## ⚡ EXECUTION INSTRUCTIONS (For Claude)

When `/eval` is invoked, follow these steps:

### Step 1: Parse Arguments
```
/eval [target] [flags]

Examples:
  /eval madhav              # Eval the madhav agent
  /eval obsidian            # Eval the obsidian MCP
  /eval --list              # List all components
  /eval madhav --generate   # Force regenerate eval cases
  /eval madhav --verbose    # Show detailed output
  /eval madhav --limit 5    # Only run 5 samples
  /eval secure              # Run both security review + config scan
  /eval secure review       # OWASP top 10 code review only
  /eval secure scan         # Claude Code config scan only
```

### Step 2: Run the Eval

**Option A: Use the Python runner (preferred)**
```bash
python3 "$SKILL_DIR/run_eval.py" [target] [flags]
```
Where `$SKILL_DIR` is the directory containing this skill (typically `skills/eval/` in the repo).

**Option B: Direct Inspect AI (optional, if installed and evals/inspect/ exists)**
```bash
# Requires: pip install inspect-ai
cd /path/to/component
inspect eval evals/inspect/*_eval.py --model anthropic/claude-sonnet-4-20250514
```
**Note**: Inspect AI is optional. The Python runner (Option A) works without it.

### Step 3: Analyze Results

After running, the skill should:
1. **Show summary** - Pass/fail counts, accuracy
2. **List failures** - Which cases failed and why
3. **Suggest improvements** - Specific fixes based on failure patterns

### Step 4: Output Format

See the [Output Format](#output-format) section below.

### Component Locations

| Type | Search Paths |
|------|--------------|
| Skills | `skills/` (relative to repo root) |

### Special Commands

- `/eval --list` → List all evaluatable components
- `/eval [target] --generate` → Force regenerate eval cases even if they exist
- `/eval [target] --skip-run` → Only generate cases, don't run eval
- `/eval secure` → Run both security code review + config scan
- `/eval secure review` → OWASP top 10 code review only
- `/eval secure scan` → Claude Code config scan only

---

Inspired by: [DeepEval](https://github.com/confident-ai/deepeval), [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai), [OpenAI Evals](https://github.com/openai/evals), [RAGAS](https://github.com/explodinggradients/ragas)

## Quick Reference

```
/eval [component]           # Run all evals for component
/eval [component] --category functional  (planned)
/eval --list                # List available components
/eval --verbose             # Detailed output per test
/eval --save                # Save results to Obsidian (planned)
```

## Core Concepts

### 1. EvalCase (Test Case Structure)

Every evaluation uses a standardized test case:

```python
@dataclass
class EvalCase:
    # Required
    id: str                         # Unique identifier
    input: Any                      # What to test (prompt, args, task)

    # Optional
    expected_output: Optional[Any]  # Ground truth (if available)
    context: List[str]              # Factual context for grounding
    metadata: Dict[str, Any]        # Tags, category, difficulty

    # Runtime (filled during execution)
    actual_output: Optional[Any]    # What was produced
    tools_called: List[ToolCall]    # For agent/MCP evals
    execution_trace: List[Step]     # For debugging
    latency_ms: int                 # Performance tracking
```

### 2. Metrics (Scoring System)

Every metric produces:
- **Score**: 0.0 to 1.0 (normalized)
- **Reason**: Explanation of the score
- **Pass/Fail**: Based on threshold (default 0.7)

```python
@dataclass
class MetricResult:
    name: str
    score: float        # 0.0 - 1.0
    threshold: float    # Pass if score >= threshold
    passed: bool
    reason: str         # Why this score?
```

### 3. Evaluation Levels

| Level | Description | When to Use |
|-------|-------------|-------------|
| **End-to-End** | Black box: input → output | Does it accomplish the task? |
| **Component** | Test individual parts | Debugging, targeted testing |
| **Smoke Test** | Quick sanity check | CI/CD gates, health checks |

## Universal Metric Categories

These apply to ANY component (MCP, Agent, Skill):

### Correctness Metrics
| Metric | Description | Grading Method |
|--------|-------------|----------------|
| **TaskCompletion** | Did it accomplish the goal? | LLM-as-judge |
| **OutputValidity** | Is output well-formed? | Schema validation |
| **FactualAccuracy** | Is output factually correct? | LLM + context grounding |

### Quality Metrics
| Metric | Description | Grading Method |
|--------|-------------|----------------|
| **Coherence** | Is output logically structured? | LLM-as-judge |
| **Completeness** | Are all requirements addressed? | Checklist matching |
| **Formatting** | Does output match expected format? | Regex/schema |

### Efficiency Metrics
| Metric | Description | Grading Method |
|--------|-------------|----------------|
| **StepEfficiency** | Minimal steps to complete? | Count comparison |
| **TokenEfficiency** | Reasonable token usage? | Threshold check |
| **Latency** | Response time acceptable? | Threshold check |

### Safety Metrics
| Metric | Description | Grading Method |
|--------|-------------|----------------|
| **NoHarmfulContent** | No toxic/biased output? | Classifier |
| **NoPIILeakage** | No sensitive data exposed? | Pattern matching |
| **ErrorHandling** | Graceful failure on bad input? | Exception handling |

### Component-Specific Metrics

**For MCPs:**
| Metric | Description |
|--------|-------------|
| ToolCorrectness | Right tool called with right args? |
| ResponseFormat | Returns markdown/structured data? |
| AuthHandling | Proper auth error messages? |

**For Agents:**
| Metric | Description |
|--------|-------------|
| PlanQuality | Logical, complete plan? |
| PlanAdherence | Follows its own plan? |
| SelfCorrection | Recovers from mistakes? |
| ToolSelection | Picks appropriate tools? |

**For Skills:**
| Metric | Description |
|--------|-------------|
| Idempotency | Same input → same output? |
| FileIntegrity | Creates expected files? |
| ConfigParsing | Handles SKILL.md correctly? |

## Grading Methods

### 1. Deterministic (Fast, Reliable)
```python
# Exact match
score = 1.0 if actual == expected else 0.0

# Contains
score = 1.0 if substring in actual else 0.0

# Regex
score = 1.0 if re.match(pattern, actual) else 0.0

# JSON Schema
score = 1.0 if validate(actual, schema) else 0.0
```

### 2. LLM-as-Judge (Flexible, Nuanced)
```python
# G-Eval pattern from DeepEval
prompt = f"""
Evaluate the following output against these criteria:
{criteria}

Input: {input}
Output: {actual_output}
Expected: {expected_output}

Score from 0-10 and explain your reasoning.
"""
```

### 3. Reference-Free (No Ground Truth Needed)
```python
# RAGAS-style: evaluate against provided context only
score = faithfulness(output, context)  # Is it grounded?
score = relevancy(output, input)       # Does it address the question?
```

### 4. Composite (Multiple Methods)
```python
# Weighted combination
final_score = (
    0.4 * correctness_score +
    0.3 * quality_score +
    0.2 * efficiency_score +
    0.1 * safety_score
)
```

## Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. DETECT COMPONENT TYPE                               │
│     └── MCP? Agent? Skill? (from name or location)      │
├─────────────────────────────────────────────────────────┤
│  2. LOAD EVAL CASES                                     │
│     ├── From evals/*.json if exists                     │
│     ├── Or generate smoke tests dynamically             │
│     └── Or use component registry defaults              │
├─────────────────────────────────────────────────────────┤
│  3. SELECT METRICS                                      │
│     ├── Universal metrics (always run)                  │
│     ├── Component-specific metrics                      │
│     └── Category filter if specified                    │
├─────────────────────────────────────────────────────────┤
│  4. EXECUTE TESTS                                       │
│     ├── Run each EvalCase through component             │
│     ├── Capture actual_output + trace                   │
│     └── Handle timeouts/errors gracefully               │
├─────────────────────────────────────────────────────────┤
│  5. SCORE RESULTS                                       │
│     ├── Apply each metric to each case                  │
│     ├── Aggregate scores                                │
│     └── Determine pass/fail                             │
├─────────────────────────────────────────────────────────┤
│  6. REPORT                                              │
│     ├── Summary table                                   │
│     ├── Failed cases with reasons                       │
│     └── Recommendations for fixes                       │
└─────────────────────────────────────────────────────────┘
```

## Output Format

```
======================================================================
🧪 EVALUATION: [component-name]
======================================================================
Type: MCP | Agent | Skill
Location: /path/to/component
Timestamp: 2026-01-21 20:00:00
Categories: functional, safety

----------------------------------------------------------------------
📋 EVAL CASES
----------------------------------------------------------------------

Case 1: [case-id]
  Input: [truncated input]
  ✓ TaskCompletion    0.95  "Successfully completed the task"
  ✓ OutputValidity    1.00  "Valid markdown format"
  ✓ Latency           0.80  "245ms (threshold: 500ms)"

Case 2: [case-id]
  Input: [truncated input]
  ✓ TaskCompletion    0.85  "Mostly complete, minor issues"
  ✗ ErrorHandling     0.40  "Crashed on empty input"

----------------------------------------------------------------------
📊 SUMMARY
----------------------------------------------------------------------

| Metric          | Passed | Failed | Avg Score |
|-----------------|--------|--------|-----------|
| TaskCompletion  | 5/5    | 0/5    | 0.92      |
| OutputValidity  | 5/5    | 0/5    | 1.00      |
| ErrorHandling   | 3/5    | 2/5    | 0.68      |
| Latency         | 4/5    | 1/5    | 0.75      |

Overall: 17/20 passed (85%)
Status: ⚠️ NEEDS ATTENTION

----------------------------------------------------------------------
🔧 RECOMMENDATIONS
----------------------------------------------------------------------
1. Fix error handling for empty inputs (Case 2, 4)
2. Optimize latency for large inputs (Case 3)

======================================================================
```

## Writing Eval Cases

### File-Based (Recommended for CI/CD)

Create `evals/cases.json` in component directory:

```json
{
  "component": "obsidian-mcp",
  "version": "1.0",
  "cases": [
    {
      "id": "read-existing-note",
      "category": "functional",
      "input": {"tool": "read_note", "args": {"path": "Code/Tips.md"}},
      "expected": {"contains": "Claude Code"},
      "metrics": ["TaskCompletion", "OutputValidity"]
    },
    {
      "id": "read-missing-note",
      "category": "error-handling",
      "input": {"tool": "read_note", "args": {"path": "nonexistent.md"}},
      "expected": {"error_contains": "not found"},
      "metrics": ["ErrorHandling"]
    },
    {
      "id": "search-content",
      "category": "functional",
      "input": {"tool": "search", "args": {"query": "Claude"}},
      "expected": {"min_results": 1},
      "metrics": ["TaskCompletion", "Latency"]
    }
  ]
}
```

### Dynamic Generation (For Quick Testing)

If no eval file exists, generate smoke tests:

```python
def generate_smoke_tests(component):
    """Generate basic smoke tests for any component."""
    tests = []

    if component.type == "MCP":
        for tool in component.tools:
            # Test with valid input
            tests.append(EvalCase(
                id=f"{tool.name}-valid",
                input=tool.example_input,
                metrics=["TaskCompletion", "OutputValidity"]
            ))
            # Test with empty input
            tests.append(EvalCase(
                id=f"{tool.name}-empty",
                input={},
                metrics=["ErrorHandling"]
            ))

    return tests
```

## Component Registry

Location: repo root `skills/`

### Skills (skills/)

| Name | Has Eval File | Notes |
|------|---------------|-------|
| build | ✅ | Dev workflow |
| decide | ⬜ | Decision framework |
| eval | ✅ | This skill |
| focus | ⬜ | Brain dump → action plan |
| researcher | ⬜ | Research vault traversal |
| search | ✅ | Deep research |
| sync | ✅ | Notion/Plaud → Obsidian |

## Flags

| Flag | Description |
|------|-------------|
| `--category X` | Only run evals in category X (planned) |
| `--verbose`, `-v` | Show all test details |
| `--save` | Save to Obsidian vault (planned) |
| `--json` | Output as JSON (planned) |
| `--list` | List available components |
| `--skip-write` | Skip write/delete operations (planned) |
| `--generate` | Generate eval cases file |
| `--native`, `-n` | Use component's own eval framework |
| `--limit N`, `-l N` | Limit number of cases to run |
| `--golden` | Use golden dataset if available |
| `--auto` | Auto-generate cases if none exist |
| `--skip-run` | Generate eval file without running |

## Advanced: Custom Metrics

Create component-specific metrics in `evals/metrics.py`:

```python
from eval_framework import Metric, MetricResult

class MarkdownQuality(Metric):
    """Check if output is well-formatted markdown."""

    name = "MarkdownQuality"
    threshold = 0.8

    def measure(self, case: EvalCase) -> MetricResult:
        output = case.actual_output

        checks = [
            ("has_headers", bool(re.search(r'^#+\s', output, re.M))),
            ("has_formatting", any(c in output for c in ['**', '_', '`'])),
            ("no_broken_links", '](broken' not in output),
            ("proper_lists", not re.search(r'^\s*[-*]\s*$', output, re.M)),
        ]

        passed = sum(1 for _, v in checks if v)
        score = passed / len(checks)

        failed = [name for name, v in checks if not v]
        reason = f"Passed {passed}/{len(checks)}" + (f", failed: {failed}" if failed else "")

        return MetricResult(
            name=self.name,
            score=score,
            threshold=self.threshold,
            passed=score >= self.threshold,
            reason=reason
        )
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Eval
on: [push, pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evals
        run: |
          claude --eval ${{ matrix.component }} --json > results.json
      - name: Check results
        run: |
          python -c "
          import json
          r = json.load(open('results.json'))
          if r['pass_rate'] < 0.8:
              exit(1)
          "
```

## Creating Evals (Prompt Template)

When asked to create evals for a component, use this prompt internally:

```
Create a comprehensive evaluation suite for this [agent/MCP/skill].

See the [References](#references) section at the end of this document for the full framework list.

## Required Deliverables

1. **evals/cases.json** - 5-10 test cases per category:
   - `functional`: Happy path, core features work
   - `error-handling`: Graceful failures, edge cases
   - `safety`: No harmful outputs, PII protection
   - `performance`: Latency, efficiency checks

2. **Test Case Structure** (per EvalCase in this framework):
   ```json
   {
     "id": "unique-test-id",
     "category": "functional|error-handling|safety|performance",
     "input": {"tool": "...", "args": {...}},
     "expected": {"contains": "...", "min_results": N, "error_contains": "..."},
     "metrics": ["TaskCompletion", "OutputValidity", "ErrorHandling"]
   }
   ```

3. **Metrics Selection** (from Universal Metric Categories above):
   - Correctness: TaskCompletion, OutputValidity, FactualAccuracy
   - Quality: Coherence, Completeness, Formatting
   - Efficiency: StepEfficiency, Latency
   - Safety: ErrorHandling, NoPIILeakage

4. **Grading Strategy**:
   - Deterministic checks FIRST (fast, reliable)
   - LLM-as-judge for subjective criteria (G-Eval pattern)
   - Reference-free where no ground truth exists (RAGAS pattern)

## Output

Produce evals that follow the Output Format defined in this framework,
with pass/fail summary and actionable recommendations.
```

## Inspect AI Integration (AISI)

**Optional eval framework.** Install with `pip install inspect-ai` if you want to use Inspect AI evals. The built-in Python runner works without it.

### Quick Start

```bash
# Run evals for a component
inspect eval evals/madhav_routing.py

# Run with specific model
inspect eval evals/ --model anthropic/claude-3-opus-20240229

# View results in browser
inspect view
```

### Writing Inspect AI Evals

Create `evals/<component>_eval.py`:

```python
from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.scorer import model_graded_fact, includes
from inspect_ai.solver import generate, system_message

@task
def madhav_routing_eval():
    """Eval: Does madhav route to correct expert agents?"""
    return Task(
        dataset=json_dataset("evals/datasets/routing_cases.jsonl"),
        solver=[
            system_message("You are Madhav, an AI routing agent..."),
            generate(),
        ],
        scorer=model_graded_fact(
            template="""
            The agent was asked to route this question:
            {input}

            Expected routing: {target}
            Actual routing: {answer}

            Score 1 if routing is correct, 0 otherwise.
            """
        ),
    )

@task
def agent_safety_eval():
    """Eval: Does agent refuse harmful requests?"""
    return Task(
        dataset=json_dataset("evals/datasets/safety_cases.jsonl"),
        solver=generate(),
        scorer=includes(target="I cannot"),  # Should refuse
    )
```

### Dataset Format (JSONL)

```jsonl
{"input": "Should I invest $1M in crypto?", "target": "bezos,elon", "metadata": {"category": "financial"}}
{"input": "How do I scale to 1M users?", "target": "ilya,elon", "metadata": {"category": "technical"}}
{"input": "Should I fire this employee?", "target": "founder,bezos", "metadata": {"category": "people"}}
```

### CLI Usage

```bash
# Run all evals in folder
inspect eval evals/

# Run specific eval
inspect eval evals/madhav_routing.py

# With options
inspect eval evals/ --model claude-3-5-sonnet --log-dir ./logs

# Compare models
inspect eval evals/ --model claude-3-opus --model claude-3-sonnet

# View results
inspect view --log-dir ./logs
```

### Integration with /eval Skill

When you run `/eval madhav`, this skill:
1. Checks for `evals/` folder in component directory
2. Runs `inspect eval evals/` if Inspect AI files exist
3. Falls back to built-in framework if no Inspect AI evals
4. Outputs unified report format

## References

### Industry Leaders
- [DeepEval](https://github.com/confident-ai/deepeval) - 12k+ stars, pytest for LLMs, 50+ metrics
- [Opik](https://github.com/comet-ml/opik) - 12.5k stars, fastest-growing eval framework
- [EleutherAI lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness) - 11k+ stars, HuggingFace backend

### Observability + Eval
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) - OpenTelemetry-native, self-hostable
- [Langfuse](https://github.com/langfuse/langfuse) - Tracing + evaluation unified
- [RAGAS](https://github.com/explodinggradients/ragas) - Reference-free RAG evaluation

### Agent-Specific
- [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) - UK AISI, composable solvers, sandboxing
- [Anthropic Bloom](https://github.com/safety-research/bloom) - Automated behavioral evaluation
- [AgentBench](https://github.com/THUDM/AgentBench) - Multi-environment agent benchmark
- [LangChain AgentEvals](https://github.com/langchain-ai/agentevals) - Trajectory evaluation

### Safety & Red Teaming
- [Promptfoo](https://github.com/promptfoo/promptfoo) - Red teaming, pentesting, YAML configs
- [Giskard](https://github.com/Giskard-AI/giskard) - LLM security scanning

### MCP Testing
- [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) - Official debugging tool
- [FastMCP Testing](https://gofastmcp.com/patterns/testing) - Python testing patterns
- [mcp-testing-kit](https://github.com/thoughtspot/mcp-testing-kit) - JS/TS testing

### Academic
- [Stanford HELM](https://github.com/stanford-crfm/helm) - Holistic evaluation benchmark
- [SWE-bench](https://github.com/SWE-bench/SWE-bench) - Coding agent benchmark
- [WebArena](https://github.com/web-arena-x/webarena) - Browser agent benchmark

### Guides
- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - LLM-as-judge patterns
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) - Agent evaluation patterns
- [Agent Benchmark Compendium](https://github.com/philschmid/ai-agent-benchmark-compendium) - 50+ benchmarks

---

## Security Mode (`/eval secure`)

When the target is `secure`, this skill switches to security auditing mode instead of component evaluation.

### Usage

```
/eval secure              # Run both review + scan
/eval secure review       # Code security review (OWASP top 10)
/eval secure scan         # Claude Code config scan (AgentShield)
```

### Mode Routing

Parse the argument after `secure`:

| Argument | Mode |
|----------|------|
| `review` | Code security review |
| `scan` | Config scan |
| _(empty)_ | Both, sequentially |

---

### Security Review (OWASP Top 10)

Audit the current codebase for security vulnerabilities. Focus on changed files first, then expand.

#### Step 1: Identify scope

```bash
# Check for uncommitted changes (review these first)
git diff --name-only
git diff --cached --name-only

# If no changes, review recent commits
git log --oneline -10 --name-only
```

#### Step 2: Run the checklist

For each file in scope, check against the 10-point security checklist below. Report findings grouped by severity.

#### The Checklist

**1. Secrets Management**
Check for hardcoded API keys, tokens, passwords, connection strings.
- `sk-`, `sk_live`, `sk_test` (API keys)
- `password\s*=\s*["']`, `secret\s*=\s*["']` (hardcoded credentials)
- `-----BEGIN.*PRIVATE KEY-----` (private keys)
- `mongodb://`, `postgres://`, `mysql://` with credentials in URL
- `.env` files that aren't gitignored

**2. Input Validation**
Check for user input used directly without validation. All API endpoints should use Pydantic (Python) or Zod (TypeScript) schemas.

**3. SQL / NoSQL Injection**
Check for string concatenation in queries. All database queries must be parameterized.

**4. Authentication & Authorization**
Check for: tokens in localStorage, missing auth checks on protected endpoints, missing authorization (user A accessing user B's data), weak/hardcoded JWT secrets.

**5. XSS Prevention**
Check for: `dangerouslySetInnerHTML` without sanitization, `| safe` filter without sanitization, user content rendered as HTML, missing CSP headers.

**6. CSRF Protection**
Check for: state-changing operations without CSRF tokens, missing `SameSite` on cookies, `@csrf_exempt` decorators.

**7. Rate Limiting**
Check for: public API endpoints without rate limiting, auth endpoints without aggressive limits.

**8. Sensitive Data Exposure**
Check for: logging passwords/tokens/PII, stack traces in error responses, PII in URLs.

**9. Dependency Vulnerabilities**
```bash
pip audit 2>/dev/null || echo "pip-audit not installed"
npm audit 2>/dev/null || echo "No package.json"
```

**10. File & Path Security**
Check for: path traversal, unrestricted file uploads, serving user-uploaded files from same domain.

#### Step 3: Report

```markdown
# Security Review - [Date]

**Scope:** [N files reviewed]
**Grade:** [A-F based on findings]

## Critical (fix now)
- [ ] **[File:line]** — [Description]
  **Fix:** [Remediation]

## High (fix before merge)
- [ ] **[File:line]** — [Description]

## Passed
- [x] Secrets management — No hardcoded secrets found
- [x] Input validation — All endpoints validated
```

---

### Config Scan (AgentShield)

Scan Claude Code configuration files for security misconfigurations.

#### With AgentShield (preferred)

```bash
npx ecc-agentshield scan
npx ecc-agentshield scan --min-severity medium
npx ecc-agentshield scan --fix  # Auto-fix safe issues
```

| Grade | Score | Action |
|-------|-------|--------|
| A (90-100) | Secure | No action needed |
| B (75-89) | Minor issues | Fix when convenient |
| C (60-74) | Needs attention | Fix before sharing configs |
| D (40-59) | Significant risks | Fix immediately |
| F (0-39) | Critical | Stop and fix now |

#### Without AgentShield (manual scan)

Check these files using Glob and Grep:

- **CLAUDE.md**: hardcoded secrets, `auto-run` instructions, overly broad tool permissions
- **settings.json**: `Bash(*)` in allow lists, missing deny lists, `--dangerously-skip-permissions`
- **MCP configs**: hardcoded env secrets, `npx -y` auto-install, unsandboxed shell-executing servers
- **Hooks**: `${file}` interpolation in commands (injection), `2>/dev/null || true` silencing errors, data exfiltration to external URLs

#### Report

```markdown
# Config Scan - [Date]

**Tool:** [AgentShield / Manual]
**Grade:** [A-F]

## Findings
### Critical
- [ ] [File] — [Issue]

### Passed
- [x] No hardcoded secrets in configs
- [x] Permissions properly scoped
```

---

### Pre-Deployment Checklist

Quick checklist for before any deploy:

- [ ] No hardcoded secrets in code or configs
- [ ] All user inputs validated (Pydantic/Zod schemas)
- [ ] All database queries parameterized
- [ ] Auth + authz checks on every protected endpoint
- [ ] Rate limiting on public and auth endpoints
- [ ] No sensitive data in logs or error responses
- [ ] Dependencies audited (`pip audit` / `npm audit`)
- [ ] `.env` files in `.gitignore`
- [ ] HTTPS enforced in production
- [ ] Claude Code configs properly scoped (no `Bash(*)`)

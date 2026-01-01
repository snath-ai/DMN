# Lár Agent Request Template

**Goal**: [Describe what the agent should do, e.g., "Analyze a PDF and extract financial tables"]

**Inputs**:
- [e.g., PDF File Path]
- [e.g., User Query]

**Tools Needed**:
- [e.g., PDF Parser]
- [e.g., Search Tool]

**Constraints**:
- [ ] Use `gemini-1.5-pro` for reasoning.
- [ ] Must be air-gap compatible (no external APIs besides the LLM).
- [ ] Output must be valid JSON matching the `FinancialReport` schema.

---
**Instruction to IDE**:
Reference `@lar/IDE_MASTER_PROMPT.md` for the coding standards.
Generate the `lar` code for this agent in a single file named `agent.py`.
Include a verification block at the bottom to run it immediately.

---
name: create-planning-document
description: Create a Nuitka planning document under `.planning/` from the standard template. Use when the user asks to create, draft, or start a planning document, and wait for explicit user authorization before implementation.
---

This workflow is used to create a new planning document in `.planning/`.

1. Ask the user for the name and the topic of the planning document if not provided.
2. Formulate the filename (all lowercase with underscores, e.g., `feature_name.md`), determine the
   target version, and automatically create the file `.planning/<filename>` with the following
   template:

```markdown
# <Title/Topic>

## Objective

<Description of the objective>

## Schedule

- **Target Version**: <Nuitka version, e.g., Nuitka 4.1>
- **Nature**: <Nature of change, e.g., Feature Enhancement, Refactoring>
- **Start Date**: <Current Date>

## Status

**Current State**: DRAFTING (Planning Phase)

- [ ] Initial research
- [ ] Requirements gathering

## Notes

(Add research notes here)

# Implementation Plan

This plan outlines the approach to...

## User Review Required

> [!IMPORTANT] <Add any important notes for user review here, or remove this section if none>

## Proposed Changes

### Step 1: <Topic>

#### [PROPOSED] [Filename](file://...)

- <Changes to make>

## Verification Plan

### Automated Tests

- <Tests to create or run>

### Manual Verification

- <Manual steps>

## External Actions checklist

- [ ] **Nuitka-Website** (Documentation):
- [ ] **Roadmap**:
```

3. Notify the user that the planning document has been created and they can now start filling it in.

4. IMPORTANT: Do NOT ask the user if they want you to begin writing code or implementing the plan.
   The user will decide when to implement and will instruct you when they are ready. Wait for their
   instructions and do not prompt them.

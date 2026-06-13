# DBT-001 — DecisionMaking skill metadata and operational guidance are stale

> **Category:** DBT
> **Severity:** Medium
> **Status:** resolved
> **Resolved:** 2026-06-12
> **Filed:** 2026-06-12
> **Affected:** `.skills/decisionmemory/SKILL.md:4`, `.skills/decisionmemory/SKILL.md:5`, `.skills/decisionmemory/SKILL.md:7`, `.skills/decisionmemory/SKILL.md:95`, `decisionmemory-plugin/skills/decision_making-memory/SKILL.md:3`, `decisionmemory-plugin/skills/decision_making-memory/SKILL.md:56`, `decisionmemory-plugin/skills/decision_making-memory/SKILL.md:82`

## Summary

The skill files contain inaccurate triggering, scoring, tool-count, and memory-write guidance. Agents can fail to activate the skill, invoke tools incorrectly, or explain recall behavior inaccurately.

## Evidence

- The top-level description does not state when to use the skill.
- The plugin description includes overly broad triggers such as generic `performance` and `confidence`.
- The documented additive 40/30/20/10 scoring conflicts with the implemented multiplicative five-factor model and power-law decay.
- `remember_decision` is described as writing all five layers, but prospective memory is created separately.
- Version `0.5.1` conflicts with package version `0.5.2`.
- The skill advertises 17 tools, documents 15, while the MCP server registers 20.
- Tool tables omit required argument contracts.

## Root cause

Skill documentation evolved independently from implementation and contains static marketing claims that are not verified during release work.

## Suggested fix

- Rewrite descriptions around qualified decision_making intents and explicit activation cases.
- Document the implemented scoring model and actual memory layers touched by each tool.
- Generate or validate tool inventory/signatures from MCP registration.
- Remove brittle test-count claims and synchronize package version metadata.
- Move installation and long reference material behind progressive-disclosure references.
- Add a release check that compares skill claims with registered tools and package metadata.

## Resolution

The packaged skill now matches package version 0.5.2, documents all 20
registered tools and their signatures, describes the implemented
multiplicative five-factor scoring model, and distinguishes prospective plans
from the layers written by `remember_decision`. Contract tests prevent these
claims from drifting from implementation metadata.

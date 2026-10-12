# AI Opportunity Bot — exploratory prototype

**Status: incomplete / not independently validated.**

This repository explores collecting job and internship listings and eventually matching them to user preferences. It is **not** a verified service that searches 100+ websites, and no production matching results, users, or deployment are established here.

## Current source inventory

The repository currently contains site-specific crawler/parser modules for:
- Indeed
- Internshala
- LinkedIn

**Important implementation issue:** the three crawler constructors pass `source_name`, `base_url` and `delay` to the base crawler, while the committed `BaseCrawler.__init__` currently only accepts `rate_limit`. This must be fixed and tested before these classes can be described as runnable.

## What is needed before a product claim

- Reconcile the base crawler API with its concrete implementations.
- Add mocked-fixture parser tests and an end-to-end controlled smoke test.
- Check source permissions/rate limits and prefer authorized data access.
- Implement and evaluate personalized relevance scoring against labeled examples.
- Document actual supported sources and known limitations.

Until those checks are complete, treat this repository as exploratory code, not a shipped AI opportunity-discovery product.

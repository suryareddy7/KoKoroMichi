# KoKoroMichi Unified Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Refactor Summary](#architecture--refactor-summary)
3. [Battle Engine Documentation](#battle-engine-documentation)
4. [Store System Documentation](#store-system-documentation)
5. [Developer & Deployment Guides](#developer--deployment-guides)
6. [Checklists & Status](#checklists--status)
7. [Appendix: File Reference](#appendix-file-reference)

---

## 1. Project Overview

KoKoroMichi is a production-ready, modular Discord bot with SaaS-ready, multi-tenant architecture, robust transactional store, advanced battle engine, and cloud deployment support. It features async data providers (local, MongoDB, Postgres), transactional services, and comprehensive documentation for maintainability and scalability.

---

## 2. Architecture & Refactor Summary

### Refactor Implementation Summary

(From `REFACTOR_SUMMARY.md`)

- Async DataProvider abstraction with multiple adapters (LocalJSON, MongoDB, Postgres)
- Services layer (StoreService, transactional API)
- All commands fallback to legacy data_manager for safety
- Robust caching, debounced I/O, centralized logging
- Docker, CI/CD, migration tools, and comprehensive documentation
- 100% backward compatible

**How to Use:**
- Local: `python bot.py` (after venv, install, .env)
- Docker: `docker-compose up -d`
- Switch to Mongo/Postgres: set `PROVIDER` env var
- Migrate data: `scripts/migrate_json_to_db.py`

---

## 3. Battle Engine Documentation

### Battle Engine Files & Summary

(From `BATTLE_ENGINE_FILES.md`, `BATTLE_ENGINE_MIGRATION.md`, `BATTLE_ENGINE_SUMMARY.md`)

- Modular, deterministic, async-first battle engine
- Core files: `core/battle_models.py`, `core/battle_balance.py`, `core/battle_engine.py`, `core/arena_queue.py`
- Features: turn order, buffs/debuffs, status effects, event logs, concurrency-safe queue
- Integration: Discord commands (`arena_new.py`), async provider fallback
- Testing: 25+ unit tests, benchmarks, performance targets met
- Migration guide, API reference, troubleshooting, and rollback plan

---

## 4. Store System Documentation

### Store System Complete Summary

(From `STORE_SYSTEM_COMPLETE.md`, `STORE_MIGRATION.md`, `STORE_COMMANDS.md`, `STORE_DELIVERY.md`)

- Three-layer design: Discord UI → StoreService → Models/Catalog
- Transactional, offline-first, idempotent, deterministic pricing
- Core files: `core/store_models.py`, `services/store_service.py`, `commands/store.py`, `data/store_catalog.json`
- Admin/user commands, VIP system, multi-currency, optimistic locking
- Comprehensive tests (14+), migration guide, troubleshooting, and delivery summary

---

## 5. Developer & Deployment Guides

### Developer Quick Reference & Module Guide

(From `DEVELOPER_MODULES.md`, `DEVELOPER_QUICKREF.md`)

- How to start, configure, and extend the bot
- Provider selection, transaction API, adding new services/providers
- Environment variables, Docker, CI/CD, migration, and testing
- Troubleshooting and common issues

### Deployment Guide

(From `DEPLOY.md`, `SETUP.md`)

- Local, Docker, Render, Railway, Heroku, VPS/systemd deployment
- Data storage options, scaling, monitoring, backup/recovery
- Performance tips and support

---

## 6. Checklists & Status

### Completion & Verification Checklists

(From `CHECKLIST.md`, `STORE_FILES_STATUS.md`)

- Refactor, services, provider adapters, command integration, infra, deployment, documentation, and testing: 100% complete
- Store system: all core files, tests, and docs complete; legacy code archived
- Next steps: run tests, migrate items, integrate VIP, deploy

---

## 7. Appendix: File Reference

- See `STORE_FILES_STATUS.md` and `BATTLE_ENGINE_FILES.md` for detailed file-by-file breakdowns, dependencies, and status.

---

**This unified documentation merges all major markdown files for KoKoroMichi. For full details, see the original files in the repository.**

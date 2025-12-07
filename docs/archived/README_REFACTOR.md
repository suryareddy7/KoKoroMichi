# KoKoroMichi Advanced Bot - Setup & Architecture Guide

## 🎉 Refactor Complete!

KoKoroMichi has been upgraded to a **production-ready, modular architecture** with async data providers, transactional services, and deployment support for cloud platforms.

## 🏗️ New Architecture Overview

### Data Layer
- **DataProvider Interface**: Abstracted storage backend (local JSON, MongoDB, PostgreSQL)
- **LocalJSONProvider**: Default local storage with debounced writes, TTL cache, and automatic backups
- **MongoDBProvider**: Async MongoDB adapter using Motor
- **PostgresProvider**: Async PostgreSQL adapter using asyncpg
- **Append-only Ledgers**: Purchase and battle logs for audit trails

### Service Layer
- **StoreService**: Transactional purchase system with rollback support
- **TransactionAPI**: Begin/commit/rollback primitives for safe multi-step operations
- Extensible to Battle, Economy, Quests services

### Command Layer
- 31 command modules (98+ commands total)
- Migrated to use async providers with automatic fallback to legacy `data_manager`
- Zero breaking changes; gradual migration path

## 📊 What's Included

✅ **31 Command Modules** - Enhanced with async providers  
✅ **98+ Commands** - Full functionality  
✅ **Async Storage** - Non-blocking I/O with multiple backend options  
✅ **Transactions** - ACID-like operations for safe state changes  
✅ **Cloud Deployment** - Docker, CI/CD, deployment guides  
✅ **Testing** - pytest scaffold for critical modules  

... (omitted for brevity)

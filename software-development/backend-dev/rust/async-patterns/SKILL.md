---
name: async-patterns
description: "DEPRECATED — absorbed into rust-async-patterns. Do not load directly; use rust-async-patterns instead (same content, plus a 'Patterns at a Glance' table and expanded best-practices do/don't guidance)."
---

# DEPRECATED: async-patterns

> This skill has been consolidated into **rust-async-patterns**. Its unique content (the Patterns at a Glance table) was merged into that skill's SKILL.md; the shared `references/details.md` is identical. Load `rust-async-patterns` for all async Rust work.

# Rust Async Patterns (legacy)

Production patterns for async Rust programming with Tokio. Read [`references/details.md`](references/details.md) for full worked examples.

## Patterns at a Glance

| Pattern | Tools | When |
|---|---|---|
| Concurrent tasks | `JoinSet`, `buffer_unordered`, `select!` | Run multiple futures in parallel |
| Channels | `mpsc`, `broadcast`, `oneshot`, `watch` | Communicate between tasks |
| Error handling | `thiserror`, `anyhow`, `timeout` | Propagate and wrap async errors |
| Graceful shutdown | `CancellationToken`, broadcast channel | Stop tasks cleanly on signal |
| Async traits | `async_trait` | Define async interface contracts |
| Streams | `async_stream`, `StreamExt` | Process sequences of async values |
| Resource management | `RwLock`, `Semaphore`, RAII guard | Shared state and connection pools |

## Dependencies

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
futures = "0.3"
async-stream = "0.3"
async-trait = "0.1"
tokio-util = { version = "0.7", features = ["sync"] }
anyhow = "1.0"
thiserror = "1.0"
tracing = "0.1"
```

## Quick Reference

```rust
// Concurrent tasks with JoinSet
let mut set = JoinSet::new();
set.spawn(async move { fetch_data(&url).await });
while let Some(res) = set.join_next().await { /* handle */ }

// Bounded concurrency
stream::iter(items).map(|x| async move { process(x).await }).buffer_unordered(10).collect().await;

// Graceful shutdown
let token = CancellationToken::new();
tokio::select! { _ = token.cancelled() => break, _ = do_work() => {} }
signal::ctrl_c().await?; token.cancel();
```

## Detailed Examples

See [`references/details.md`](references/details.md) for complete worked patterns covering all 7 pattern categories above.

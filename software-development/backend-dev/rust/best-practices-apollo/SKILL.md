---
name: best-practices-apollo
description: Apollo GraphQL's Rust best practices handbook — coding style, linting, performance, error handling, testing, generics, type-state, documentation, and pointers. Use when writing or reviewing Rust code for idiom correctness, code quality, or style consistency.
---

# Rust Best Practices (Apollo)

Best practices handbook from Apollo GraphQL's Rust team. Read chapters relevant to the task at hand.

## Chapters

- [Chapter 1 — Coding Styles and Idioms](references/chapter_01.md): borrowing vs cloning, Copy trait, Option/Result patterns, iterators, comments, imports
- [Chapter 2 — Clippy and Linting](references/chapter_02.md): clippy setup, important lints, workspace lint config, suppression policy
- [Chapter 3 — Performance Mindset](references/chapter_03.md): flamegraph, redundant cloning, stack vs heap, zero-cost abstractions
- [Chapter 4 — Error Handling](references/chapter_04.md): Result vs panic, unwrap/expect policy, thiserror, anyhow, `?` operator
- [Chapter 5 — Automated Testing](references/chapter_05.md): test naming, one-assertion rule, snapshot testing
- [Chapter 6 — Generics and Dispatch](references/chapter_06.md): static vs dynamic dispatch, trait objects, boxing at boundaries
- [Chapter 7 — Type State Pattern](references/chapter_07.md): compile-time state safety, PhantomData, when to use it
- [Chapter 8 — Comments vs Documentation](references/chapter_08.md): when to comment, doc comments, rustdoc, doc-tests
- [Chapter 9 — Understanding Pointers](references/chapter_09.md): thread safety, Send/Sync, pointer types (Box, Arc, Rc)

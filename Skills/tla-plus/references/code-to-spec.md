# Extracting a spec from code

The usual failure is a clean textbook model that does not match the code. Asked for etcd, the agent writes the Raft paper. Build the model from the code's own transitions.

## Steps

1. Find the shared state and the per-process state that the properties depend on.
2. Find the atomic steps in the code: critical sections, lock acquisitions, message handlers, transaction boundaries. Each is a candidate action.
3. For each candidate write the exact guard and the exact update. Mirror the data operation the code performs: overwrite or union, map update or set add.
4. Abstract only after the concrete transitions are understood. Drop logging, buffers and temporaries. Keep the control and data flow that affects safety or liveness.
5. Replay real executions against the model with `--scenario` (see `modelling.md`): a test's sequence of calls, a production log, a known incident. Done when each replays, or the divergence is written down.

## Where the interleaving points are

- **Rust**: uses of `&mut` and interior mutability, and the concurrency primitives (`Mutex`, channels, atomics).
- **Go**: goroutine creation, channel operations and `select`.
- **Erlang/Elixir**: each process becomes a process identifier in the model, and each `receive` an action consuming from a mailbox variable.
- **Python and others**: the concurrent units (threads, async tasks) and the shared objects they mutate. Every `await` is an interleaving point.

## Conformance

The model is faithful when:

- every transition the code can take that matters to the properties is enabled by some action in the corresponding state
- every transition the model allows that the code cannot take is listed as a deliberate abstraction
- the state is rich enough to state the key invariants

Where code and model diverge, write the divergence down and decide which changes: the model, the code, or the level of abstraction.

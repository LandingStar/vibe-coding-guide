# CLI Command Reference

This document is synchronized with `demo/command_reference.py`.

## Overview

Commands: attack [target_id], rally, haste, extra, grant [target_id], immediate [target_id], pull [target_id], delay [target_id], poison [target_id], status, effects, sync, resync, transport, recover, ping, disconnect, reconnect, inject <client|server|both> <hp|attack|speed|round|time> ..., net, queue, send, deliver, flush, help [command|all], quit

## `attack`

- Usage: `attack [target_id]`
- Availability: Authoritative and predictive modes
- Summary: Use Basic Attack on the target, or on the default enemy when omitted.
- Details:
  - Predictive mode executes the command locally first.
  - Network simulation mode leaves the result pending until you send and deliver authority updates.
- Examples:
  - `attack`
  - `attack slime`

## `rally`

- Usage: `rally`
- Availability: Authoritative and predictive modes
- Summary: Apply ATTACK_UP to the current actor.
- Details:
  - Rally is a self-targeting skill and does not need a target id.
  - In network simulation mode, the effect becomes authoritative after send/deliver or flush.
- Examples:
  - `rally`

## `haste`

- Usage: `haste`
- Availability: Authoritative and predictive modes
- Summary: Apply HASTE to the current actor and increase Speed for upcoming timeline turns.
- Details:
  - Haste is a self-targeting skill and does not need a target id.
  - Under timeline, committed speed changes rescale the actor's remaining action value deterministically.
- Examples:
  - `haste`

## `extra`

- Usage: `extra`
- Availability: Timeline driver in authoritative and predictive modes
- Summary: Under timeline, grant the current actor one extra command window after the current turn.
- Details:
  - Current minimal grant support only covers one WindowGrantEvent shape: ENTITY_COMMAND_WINDOW + AFTER_CURRENT.
  - This is a demo command for the window-grant path, not a generalized cut-in or interrupt system.
- Examples:
  - `extra`

## `grant`

- Usage: `grant [target_id]`
- Availability: Timeline driver in authoritative and predictive modes
- Summary: Under timeline, grant another actor one extra command window after the current turn.
- Details:
  - Current foreign grant support only covers ENTITY_COMMAND_WINDOW + AFTER_CURRENT and only for a strict future target.
  - The granted actor keeps its original future AV slot; this command only inserts one temporary granted window.
- Examples:
  - `grant`
  - `grant slime`

## `immediate`

- Usage: `immediate [target_id]`
- Availability: Timeline driver in authoritative and predictive modes
- Summary: Under timeline, suspend the current actor and immediately grant another actor one command window.
- Details:
  - Current immediate insert support only covers ENTITY_COMMAND_WINDOW + IMMEDIATE and only for a strict future target.
  - The interrupted actor resumes its original window after the granted actor resolves the inserted turn.
- Examples:
  - `immediate`
  - `immediate slime`

## `pull`

- Usage: `pull [target_id]`
- Availability: Timeline driver in authoritative and predictive modes
- Summary: Under timeline, advance the target toward its next action by a normalized percent.
- Details:
  - Current advance support only covers ADVANCE + NORMALIZED_PERCENT and only for a future target.
  - The command consumes the current turn and keeps window lifecycle semantics unchanged.
- Examples:
  - `pull`
  - `pull slime`

## `delay`

- Usage: `delay [target_id]`
- Availability: Timeline driver in authoritative and predictive modes
- Summary: Under timeline, push the target farther away from its next action by a normalized percent.
- Details:
  - Current delay support only covers DELAY + NORMALIZED_PERCENT and only for a future target.
  - A sufficiently large delay can let the current actor cycle back in before the delayed target acts.
- Examples:
  - `delay`
  - `delay slime`

## `poison`

- Usage: `poison [target_id]`
- Availability: Authoritative and predictive modes
- Summary: Apply POISON to the target, or to the default enemy when omitted.
- Details:
  - Poison ticks on the poisoned target's own TURN_END.
  - In predictive + network simulation mode, the poison application stays pending until authority arrives.
- Examples:
  - `poison`
  - `poison slime`

## `status`

- Usage: `status`
- Availability: All modes
- Summary: Print the current scheduling state, active actor, HP, ATK, SPD, AV, and active effects.
- Details:
  - This is a read-only snapshot of the current local client state.
  - The leading state label depends on the active driver, for example Round under classical_turn or Time under timeline.
  - Under timeline, entity lines include AV so you can observe future turn timing changes directly.
- Examples:
  - `status`

## `effects`

- Usage: `effects`
- Availability: All modes
- Summary: Show the registered effect authoring definitions available in the current runtime.
- Details:
  - This is a developer-facing inspection command for the current effect catalog and runtime hook profiles.
  - It does not print live effect instances; use status for currently active effects on entities.
- Examples:
  - `effects`

## `sync`

- Usage: `sync`
- Availability: All modes
- Summary: Show the most recent sync/recovery status summary.
- Details:
  - The output includes kind, snapshot id, revision, current actor, and binding token.
  - Useful after predictive replay, rejection, manual resync, or automatic recovery.
- Examples:
  - `sync`

## `resync`

- Usage: `resync`
- Availability: All modes
- Summary: Pull a fresh authoritative snapshot from the server and re-apply it to the client.
- Details:
  - In predictive mode this re-runs replay for remaining pending commands.
  - In projection mode this simply overwrites the client from the latest server snapshot.
  - Under socket + predictive sessions with an active scheduler projection, a disconnected transport will first attempt one automatic recover.
- Examples:
  - `resync`

## `transport`

- Usage: `transport`
- Availability: All modes
- Summary: Show the current host transport mode, endpoint, ownership, and connection state.
- Details:
  - Useful for distinguishing local, subprocess, and socket sessions.
  - In socket mode it shows whether the client owns the server process or is attached to an external one.
  - The transport report also shows whether automatic recovery is eligible and a summary of the most recent recovery attempt.
- Examples:
  - `transport`

## `recover`

- Usage: `recover`
- Availability: Socket predictive sessions with an active scheduler projection
- Summary: Attempt a one-shot reconnect + authority recovery for the current client session.
- Details:
  - Recovery automation is available for predictive socket sessions whose current local state exposes a scheduler projection.
  - Recover reconnects if needed, then imports a fresh authoritative snapshot and replays remaining pending commands.
- Examples:
  - `recover`

## `ping`

- Usage: `ping`
- Availability: All modes
- Summary: Ping the current authority host through the active transport.
- Details:
  - For local mode this reports an immediate in-process success.
  - For subprocess and socket transports this performs an actual host request.
- Examples:
  - `ping`

## `disconnect`

- Usage: `disconnect`
- Availability: Socket transport
- Summary: Manually disconnect the active transport connection when the transport supports it.
- Details:
  - This keeps the current local client state intact and is intended for recovery testing.
  - The current implementation supports manual disconnect for socket transport only.
- Examples:
  - `disconnect`

## `reconnect`

- Usage: `reconnect`
- Availability: Socket transport
- Summary: Reconnect the active transport and immediately recover the client from authority.
- Details:
  - Reconnect performs a fresh transport attach and then runs a sync recovery from the latest server snapshot.
  - In predictive mode, any remaining pending commands are replayed after the authoritative snapshot is imported.
- Examples:
  - `reconnect`

## `inject`

- Usage: `inject <client|server|both> <hp|attack|speed|round|time> ...`
- Availability: All modes
- Aliases: `desync`
- Summary: Apply a debug snapshot mutation for desync and recovery testing.
- Details:
  - Use client to create a local desync without touching authority.
  - Use server to mutate only authority, or both to move both sides together.
  - Supported fields are hp, attack, speed, round, and time.
- Examples:
  - `inject client hp slime 1`
  - `inject server attack hero 99`
  - `inject server speed hero 18`
  - `inject both round 7`
  - `inject client time 1500`

## `net`

- Usage: `net`
- Availability: Predictive + network simulation mode
- Aliases: `pending`
- Summary: Show local loopback network state: pending, unsent, outbox, and inbox.
- Details:
  - pending counts locally predicted commands still waiting for authority resolution.
  - unsent counts pending commands not yet moved into the local outbox.
- Examples:
  - `net`
  - `pending`

## `queue`

- Usage: `queue`
- Availability: Predictive + network simulation mode
- Summary: List current pending commands and their sent state.
- Details:
  - This is the easiest way to inspect multi-pending command order before send/flush.
- Examples:
  - `queue`

## `send`

- Usage: `send`
- Availability: Predictive + network simulation mode
- Summary: Send the next queued local command through the loopback transport.
- Details:
  - If nothing is already in the outbox, the next unsent pending command is queued first.
  - A send enqueues the resulting authoritative snapshot into the local inbox.
- Examples:
  - `send`

## `deliver`

- Usage: `deliver`
- Availability: Predictive + network simulation mode
- Summary: Deliver the next authoritative snapshot from the local inbox to the client.
- Details:
  - Deliver applies the next pending authoritative sync and may trigger replay of remaining pending commands.
- Examples:
  - `deliver`

## `flush`

- Usage: `flush`
- Availability: Predictive + network simulation mode
- Summary: Process all currently queued sends and deliveries until the loopback transport is drained.
- Details:
  - Flush is the fastest way to resolve all currently pending network work.
  - It is useful for returning to a clean authoritative state after several local predictions.
- Examples:
  - `flush`

## `help`

- Usage: `help [command|all]`
- Availability: All modes
- Summary: Show command overview, or detailed help for one command.
- Details:
  - Use 'help attack' to inspect one command.
  - Use 'help all' to print the full detailed command reference inside the CLI.
- Examples:
  - `help`
  - `help attack`
  - `help all`

## `quit`

- Usage: `quit`
- Availability: All modes
- Aliases: `exit`
- Summary: Exit the CLI.
- Details:
  - exit is an alias for quit.
- Examples:
  - `quit`
  - `exit`

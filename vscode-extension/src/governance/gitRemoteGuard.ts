/**
 * Git Remote Guard — hardcoded pre-execution blocker.
 *
 * Unconditionally blocks remote git operations (push, pull, fetch,
 * remote, clone) before they reach the governance interceptor.
 * This guard cannot be overridden, configured, or exempted.
 */

/**
 * Remote git subcommands that are always blocked.
 * Only operations that MODIFY the remote are blocked.
 * Read-only remote ops (pull, fetch, clone) are allowed.
 */
const BLOCKED_SUBCOMMANDS = [
    'push',
];

/**
 * Regex that matches `git <blocked-subcommand>` at a command boundary.
 * Handles: leading whitespace, path-qualified git, quotes, &&, ;, |,
 * PowerShell & operator, and paths with spaces (quoted).
 */
const GIT_REMOTE_PATTERN = new RegExp(
    // Match git (with optional quoted or unquoted path prefix and .exe suffix)
    // followed by a blocked subcommand
    `(?:^|[;&|]|\\|\\||&&|&)\\s*` +
    `(?:"[^"]*[\\\\/])?` +                           // optional quoted path prefix like "C:\...\
    `(?:[\\w:/\\\\.-]*[\\\\/])?` +                    // optional unquoted path prefix (incl drive letter :)
    `git(?:\\.exe)?"?\\s+` +                         // git or git.exe, optional closing quote
    `(?:${BLOCKED_SUBCOMMANDS.join('|')})` +         // the blocked subcommand
    `(?:\\s|$|[;&|])`,                               // end boundary
    'i',
);

export interface GitRemoteGuardResult {
    blocked: boolean;
    /** Which subcommand was matched, if blocked. */
    matchedSubcommand: string | null;
    /** Fixed deny message (no dynamic content to prevent injection). */
    message: string | null;
}

/**
 * Check whether a command line contains a remote git operation.
 * This check is pure string-based, has no external dependencies,
 * and cannot be disabled.
 */
export function checkGitRemoteGuard(commandLine: string): GitRemoteGuardResult {
    if (!commandLine) {
        return { blocked: false, matchedSubcommand: null, message: null };
    }

    const match = GIT_REMOTE_PATTERN.exec(commandLine);
    if (!match) {
        return { blocked: false, matchedSubcommand: null, message: null };
    }

    // Extract which subcommand was matched
    const lower = match[0].toLowerCase();
    const subcommand = BLOCKED_SUBCOMMANDS.find(cmd => lower.includes(cmd)) ?? 'unknown';

    return {
        blocked: true,
        matchedSubcommand: subcommand,
        message:
            `[HARD BLOCK] "git ${subcommand}" is permanently disabled in this workspace. ` +
            'Pushing to remote repositories is blocked to prevent unintended modifications. ' +
            'Read-only operations (pull, fetch, clone) are allowed.',
    };
}

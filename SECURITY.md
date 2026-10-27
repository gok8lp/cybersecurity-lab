# Security boundary

Single owner only, behind loopback and an authenticated SSH tunnel. No multi-user authentication. Do not expose the API or broker to the LAN or Internet.

Only the private host broker has Docker permission. It accepts allowlisted challenge IDs and bounded exercise commands, never shell text, host paths or arbitrary Docker arguments. Targets have internal networks, no published ports, read-only roots, no capabilities and resource limits.

The broker is trusted: code execution in that process could cross the host boundary. The API uses a separate OS user without Docker membership. The private socket is restricted by its parent directory permissions.

Flags and commands are absent from persistent audit events. A learner sees their own flag in the console. Docker administrators can inspect container environments; administrator access is outside the learner boundary.

Report issues privately to the repository owner through GitHub's available private reporting channel. Do not include real credentials or server data in public issues.

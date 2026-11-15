# Restart: direct pilot interrupted by security filter

The corrected fresh blind dispatch passed an actual synthetic-lamp smoke test:
its controller and independent blind session completed with recorded usage,
and blind coverage passed for the one-event fixture. The estimated combined
smoke cost was $0.071886. The pre-registered $5 soft budget for this restart
included that smoke and the two new pilots; the earlier blocked attempt was
kept separate with its residual usage unknown.

The fresh direct pilot ran about 986 seconds. Its independent blind session
completed and the coverage gate reported 32 events and 82 pair orderings; it
also flagged three rows as `as-is`, meaning those expectations were not
independent predictions. Catalogue fields, matrix and guard checks exited 0.
The sidecar, reachability and deliverables gates failed because analysis.json
and manifest.json were not present when the controller stopped.

The controller ended with the platform message: "This content was flagged for
possible cybersecurity risk." The response recommended applying for Daybreak
access before retrying. This is an automated filter outcome; the exact event is
preserved in `attempt/direct/events.jsonl`. No attempt was made to bypass the
filter. The routed arm did not start. There is no valid matched comparison and
no conclusion about GEPA or Flash/Jev effectiveness.

The direct controller's last reported partial usage was approximately $0.9118916
and its completed blind session approximately $0.1033056; with the smoke, the
known restart subtotal is approximately $1.0870832. The controller turn did not
complete, so its final usage is unknown. These are rate-based estimates, not
billing statements, and exclude supervising-session costs. The earlier
attempt's known subtotal ($0.4393228) and its unknown residual cost are
additional. A repeat requires resolving the platform block and accounting
uncertainty rather than treating missing usage as zero.

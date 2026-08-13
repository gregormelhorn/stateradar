# Disposition matrix — mini

<!-- states: Idle Open Closed -->

Abstraction: flat leaf states, no hierarchy; completeness is relative
to the eight-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup | UV-M2-stale | UV-M1-lost | UV-M2-conflict | UV-M1-spurious | svc-ack |
|---|---|---|---|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` | reject `mini.py:45` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` | handle (counted) `mini.py:47` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` | ignore (documented) `mini.py:49` |

# Disposition matrix — mini

<!-- states: Idle Open Closed -->

Abstraction: flat leaf states, no hierarchy; completeness is relative
to the four-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup | UV-M2-stale |
|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |

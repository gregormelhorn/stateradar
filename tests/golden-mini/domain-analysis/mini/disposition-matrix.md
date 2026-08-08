# Disposition matrix — mini

<!-- states: Idle Open Closed -->

Abstraction: flat leaf states, no hierarchy; completeness is relative
to the three-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup |
|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` |

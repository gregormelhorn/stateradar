# Disposition matrix — mini

<!-- states: Idle Open Closed -->
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup |
|---|---|---|---|
| **Idle** | transition →Open `mini.py:10` | ignore (documented) `mini.py:20` | handle (counted) `mini.py:30` |
| **Open** | ignore (documented) `mini.py:40` | transition →Closed `mini.py:50` | handle (counted) `mini.py:60` |
| **Closed** | reject `mini.py:70` | ignore (documented) `mini.py:80` | handle (counted) `mini.py:90` |

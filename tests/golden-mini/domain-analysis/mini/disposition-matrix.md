# Disposition matrix — mini

<!-- states: idle open closed -->

| state | M1 | M2 | UV-M1-dup |
|---|---|---|---|
| **idle** | transition →open `mini.py:10` | ignore (documented) `mini.py:20` | handle (counted) `mini.py:30` |
| **open** | ignore (documented) `mini.py:40` | transition →closed `mini.py:50` | handle (counted) `mini.py:60` |
| **closed** | reject `mini.py:70` | ignore (documented) `mini.py:80` | handle (counted) `mini.py:90` |

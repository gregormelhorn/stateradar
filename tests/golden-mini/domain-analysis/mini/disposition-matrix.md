# Disposition matrix — mini

<!-- states: Idle Open Closed -->

Abstraction: flat leaf states, no hierarchy; completeness is relative
to the eight-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup | UV-M2-stale | UV-M1-lost | UV-M2-conflict | UV-M1-spurious | svc-ack |
|---|---|---|---|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` ("self.state = \"Open\"") | ignore (documented) `mini.py:28` ("return \"ignored\"") | handle (counted) `mini.py:30` ("self.dup_count += 1") | ignore (documented) `mini.py:33` ("return \"ignored\"") | ignore (documented) `mini.py:35` ("return \"ignored\"") | ignore (documented) `mini.py:37` ("return \"ignored\"") | reject `mini.py:39` ("raise RejectedError") | reject `mini.py:45` ("raise RejectedError") |
| **Open** | ignore (documented) `mini.py:22` ("return \"ignored\"") | transition →Closed `mini.py:26` ("self.state = \"Closed\"") | handle (counted) `mini.py:30` ("self.dup_count += 1") | ignore (documented) `mini.py:33` ("return \"ignored\"") | ignore (documented) `mini.py:35` ("return \"ignored\"") | ignore (documented) `mini.py:37` ("return \"ignored\"") | reject `mini.py:39` ("raise RejectedError") | handle (counted) `mini.py:47` ("self.dup_count += 1") |
| **Closed** | reject `mini.py:23` ("raise RejectedError") | ignore (documented) `mini.py:28` ("return \"ignored\"") | handle (counted) `mini.py:30` ("self.dup_count += 1") | ignore (documented) `mini.py:33` ("return \"ignored\"") | ignore (documented) `mini.py:35` ("return \"ignored\"") | ignore (documented) `mini.py:37` ("return \"ignored\"") | reject `mini.py:39` ("raise RejectedError") | ignore (documented) `mini.py:49` ("return \"ignored\"") |

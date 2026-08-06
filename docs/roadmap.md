# Remaining work plan (post-v1.33)

## 1. CONVERGENCE.md — calibration data (evidence gap)

**Problem:** README empfiehlt "run the pilot twice and diff", aber es
existiert keine einzige CONVERGENCE.md im Repo. Das ist die
Reliability-Kennzahl des Verfahrens.

**Plan:**
1. Eine Komponente auswählen, die StateRadar noch nicht analysiert hat
   (idealerweise: synthetisch oder nach Modell-Cutoff, um
   Kontaminationsprobleme zu vermeiden).
2. Zwei unabhängige Part-A-Durchläufe in frischen Sessions.
3. Matrizen diffen, Divergenz klassifizieren.
4. `CONVERGENCE.md` ins `.benchmarks/`-Verzeichnis legen.
5. Pro Release einen Durchlauf wiederholen.
6. Ziel: eine Divergenzrate über 3-5 Komponenten als Baseline etablieren.

**Aufwand:** ~1h pro Komponente, initial 2-3 Komponenten.

## 2. Synthetic example ("Device Connection")

**Problem:** `examples/` ist leer bis auf ein Disclosure-README.
Adoption braucht ein sichtbares, lauffähiges Beispiel.

**Plan:**
1. Synthetische Komponente entwerfen (~200-300 LOC):
   - Device-Connection-Manager
   - States: Disconnected, Connecting, Connected, Reconnecting, Failed
   - Events: connect, disconnect, timeout, retry, cancel
   - Inklusive README mit Anforderungen
2. Vollständigen StateRadar-Durchlauf (Part A + Part B + Diff) dokumentieren.
3. Alle Artefakte (Matrix, Statechart, Questions, Traces) ins `examples/device-connection/` legen.
4. Als `CONVERGENCE.md`-Kandidat #1 verwenden (Punkt 1).

**Aufwand:** ~2h für Komponente + Durchlauf + Dokumentation.

## 3. XState / Semantic Analysis (later door)

**Problem:** Mermaid↔Matrix-Sync ist textuelle Konsistenz, keine
Semantik. Erreichbarkeit, Simulation, Vollständigkeitsprüfung über
Hierarchie/Parallelregionen sind nicht abgedeckt.

**Plan:**
1. `analysis.json` ist bereits nah an einem maschinenlesbaren Automaten.
2. Optionaler Reachability-Checker (`tools/check_reachability.py`):
   - Liest `analysis.json`
   - Baut den Zustandsgraphen
   - Prüft: alle States erreichbar? Alle Events haben mindestens eine
     Transition? Keine Deadlocks?
3. Keine Prompt-Änderung nötig — das Schema trägt bereits alle Daten.

**Aufwand:** ~3h für ersten Prototyp, nur wenn es wehtut.

**Priorität:** Niedrig. Der aktuelle Methodenstand findet Bugs ohne
semantische Analyse. Reachability wäre nice-to-have, aber die
Grundannahme "wenn die Matrix-Lücke gefüllt ist, ist das ein Finding"
hat in 11 Piloten funktioniert.

# Pool Get and Put interleaving P-04a

The probe runs silenceper/pool at `6084537e520652192f41aebfd88d822c00b9447a`.
A Go overlay pauses the first Get immediately after it misses the idle
channel and before it locks. Put returns a held connection during that
pause. The probe then observes the first Get blocked in a channel receive
while Len reports one idle connection. A later Get claims that connection.
Returning a second held connection completes the first Get.

The overlay changes scheduling only in the behavior probe. The negative
control also rechecks the idle channel after the pause. That control fails
the probe because the first Get returns early. Both runs use the Go race
detector. The test does not decide the intended behavior.

```sh
python3 docs/evidence/pool-p04a/reproduce.py /path/to/pool
python3 docs/evidence/pool-p04a/reproduce.py /path/to/pool --control
```

The pair identifier is local to the catalogue in PR #13. Match the
sequence when comparing other runs.

package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

func TestIdentityCallerVariableRebinding(t *testing.T) {
	original := &fixture.Account{Epoch: 7}
	replacement := &fixture.Account{Epoch: 7}
	port := &fixture.Port{Target: original}
	originalPort := port
	replacementPort := &fixture.Port{Target: replacement}

	counters(t, original, 0, 0)
	counters(t, replacement, 0, 0)
	complete := fixture.F(port)
	counters(t, original, 1, 0)
	counters(t, replacement, 0, 0)
	port = replacementPort

	if originalPort == port || originalPort.Target != original || port.Target != replacement {
		t.Fatal("caller reassignment did not leave two distinct Ports with their original targets")
	}
	counters(t, original, 1, 0)
	counters(t, replacement, 0, 0)

	complete()

	if originalPort.Target != original || port.Target != replacement {
		t.Fatal("completion changed a Port target")
	}
	counters(t, original, 1, 1)
	counters(t, replacement, 0, 0)
}

func TestIdentityRetainedPort(t *testing.T) {
	for _, op := range []struct {
		name              string
		admit             func(*fixture.Port) func()
		incomingSuccesses int
	}{
		{"A", (*fixture.Port).A, 1},
		{"C", (*fixture.Port).C, 0},
	} {
		t.Run(op.name, func(t *testing.T) {
			original := &fixture.Account{Epoch: 7}
			separate := &fixture.Account{Epoch: 7}
			incoming := &fixture.Account{Epoch: 7}
			port := &fixture.Port{Target: original}
			originalPort := port
			complete := op.admit(port)
			port = &fixture.Port{Target: separate}

			if originalPort.Target != original || port.Target != separate {
				t.Fatal("caller reassignment changed a target")
			}
			counters(t, original, 1, 0)
			complete()
			counters(t, original, 1, 1)
			counters(t, separate, 0, 0)

			originalPort.Target = incoming
			complete()
			counters(t, original, 1, 1)
			counters(t, separate, 0, 0)
			counters(t, incoming, 0, op.incomingSuccesses)
		})
	}
}

func TestIdentityRetainedRegistryAndKey(t *testing.T) {
	original := &fixture.Account{Epoch: 7}
	otherKey := &fixture.Account{Epoch: 7}
	otherRegistry := &fixture.Account{Epoch: 7}
	newOccupant := &fixture.Account{Epoch: 8}
	callerKey := "old"
	registry := &fixture.Registry{Entries: map[string]*fixture.Account{
		callerKey: original, "new": otherKey,
	}}
	originalRegistry := registry
	complete := registry.D(callerKey)

	callerKey = "new"
	counters(t, registry.Entries[callerKey], 0, 0)
	counters(t, original, 1, 0)
	complete()
	counters(t, original, 1, 1)
	counters(t, otherKey, 0, 0)

	registry = &fixture.Registry{Entries: map[string]*fixture.Account{"old": otherRegistry}}
	counters(t, registry.Entries["old"], 0, 0)
	complete()
	counters(t, original, 1, 2)
	counters(t, otherKey, 0, 0)
	counters(t, otherRegistry, 0, 0)

	originalRegistry.Entries["old"] = newOccupant
	complete()
	counters(t, original, 1, 2)
	counters(t, otherKey, 0, 0)
	counters(t, otherRegistry, 0, 0)
	counters(t, newOccupant, 0, 1)
}

func TestIdentityAccountCopyAndOverwrite(t *testing.T) {
	original := &fixture.Account{Epoch: 7}
	port := &fixture.Port{Target: original}
	complete := port.C()
	copied := *original
	port.Target = &copied
	complete()
	counters(t, original, 1, 0)
	counters(t, &copied, 1, 0)

	port.Target = original
	*original = fixture.Account{Successes: 10, Epoch: 7}
	counters(t, original, 0, 10)
	complete()
	counters(t, original, 0, 11)
	counters(t, &copied, 1, 0)
}

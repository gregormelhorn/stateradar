package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

func TestIdentityCallerVariableRebinding(t *testing.T) {
	original := &fixture.Account{Epoch: 7}
	incoming := &fixture.Account{Epoch: 8}
	var callerPort *fixture.Port = &fixture.Port{Target: original}
	originalPort := callerPort
	incomingPort := &fixture.Port{Target: incoming}
	complete := fixture.F(callerPort)

	callerPort = incomingPort
	checkState := func(wantSuccesses int) {
		t.Helper()
		if callerPort == originalPort || callerPort != incomingPort {
			t.Fatal("caller variable does not point to the distinct replacement port")
		}
		if originalPort.Target != original || incomingPort.Target != incoming {
			t.Fatal("a port target changed")
		}
		if original.Epoch != 7 || incoming.Epoch != 8 {
			t.Fatal("an account epoch changed")
		}
		counters(t, original, 1, wantSuccesses)
		counters(t, incoming, 0, 0)
	}
	checkState(0)
	complete()
	checkState(1)
}

func TestIdentityRegistryOtherKeyAlias(t *testing.T) {
	b := newBinding()
	b.registry.Entries["other"] = b.original
	complete := b.registry.D(key)
	counters(t, b.original, 1, 0)

	delete(b.registry.Entries, key)
	complete()
	counters(t, b.original, 1, 0)
	if b.registry.Entries["other"] != b.original {
		t.Fatal("the other key no longer points to the admitted account")
	}

	b.registry.Entries[key] = b.original
	counters(t, b.original, 1, 0)
	complete()
	counters(t, b.original, 1, 1)
}

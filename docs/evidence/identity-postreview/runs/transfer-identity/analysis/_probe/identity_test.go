package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

const key = "work"

type binding struct {
	original *fixture.Account
	port     *fixture.Port
	registry *fixture.Registry
}

func newBinding() binding {
	original := &fixture.Account{Epoch: 7}
	return binding{
		original: original,
		port:     &fixture.Port{Target: original},
		registry: &fixture.Registry{Entries: map[string]*fixture.Account{key: original}},
	}
}

type operation struct {
	name  string
	admit func(binding) func()
}

var operations = []operation{
	{"A", func(b binding) func() { return b.port.A() }},
	{"B", func(b binding) func() { return b.port.B() }},
	{"C", func(b binding) func() { return b.port.C() }},
	{"D", func(b binding) func() { return b.registry.D(key) }},
	{"E", func(b binding) func() { return b.port.E() }},
	{"F", func(b binding) func() { return fixture.F(b.port) }},
}

func (b binding) replace(op operation, account *fixture.Account) {
	if op.name == "D" {
		b.registry.Entries[key] = account
	} else {
		b.port.Target = account
	}
}

func eachOperation(t *testing.T, run func(*testing.T, operation, binding)) {
	t.Helper()
	for _, op := range operations {
		t.Run(op.name, func(t *testing.T) { run(t, op, newBinding()) })
	}
}

func counters(t *testing.T, account *fixture.Account, requests, successes int) {
	t.Helper()
	if account.Requests != requests || account.Successes != successes {
		t.Fatalf("counters = (%d requests, %d successes), want (%d, %d)", account.Requests, account.Successes, requests, successes)
	}
}

func mustPanic(t *testing.T, action func()) {
	t.Helper()
	defer func() {
		if recover() == nil {
			t.Error("expected a panic")
		}
	}()
	action()
}

func TestIdentityBaseline(t *testing.T) {
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		complete := op.admit(b)
		counters(t, b.original, 1, 0)
		complete()
		counters(t, b.original, 1, 1)
	})
}

func replacement(t *testing.T, epoch int, expected map[string][2]int) {
	t.Helper()
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		incoming := &fixture.Account{Epoch: epoch}
		complete := op.admit(b)
		b.replace(op, incoming)
		counters(t, b.original, 1, 0)
		counters(t, incoming, 0, 0)
		complete()
		counters(t, b.original, 1, expected[op.name][0])
		counters(t, incoming, 0, expected[op.name][1])
	})
}

func TestIdentitySameEpochReplacement(t *testing.T) {
	replacement(t, 7, map[string][2]int{
		"A": {0, 1}, "B": {1, 0}, "C": {0, 0}, "D": {0, 1}, "E": {1, 0}, "F": {1, 0},
	})
}

func TestIdentityDifferentEpochReplacement(t *testing.T) {
	replacement(t, 8, map[string][2]int{
		"A": {0, 0}, "B": {1, 0}, "C": {0, 0}, "D": {0, 1}, "E": {1, 0}, "F": {1, 0},
	})
}

func TestIdentityEpochChange(t *testing.T) {
	expected := map[string]int{"A": 0, "B": 1, "C": 0, "D": 1, "E": 1, "F": 1}
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		complete := op.admit(b)
		b.original.Epoch = 8
		counters(t, b.original, 1, 0)
		complete()
		counters(t, b.original, 1, expected[op.name])
	})
}

func TestIdentityCompletionBeforeBoundary(t *testing.T) {
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		incoming := &fixture.Account{Epoch: 8}
		complete := op.admit(b)
		complete()
		counters(t, b.original, 1, 1)
		b.original.Epoch = 8
		if op.name == "D" {
			delete(b.registry.Entries, key)
			counters(t, b.original, 1, 1)
		} else {
			b.port.Target = nil
			counters(t, b.original, 1, 1)
		}
		b.replace(op, incoming)
		counters(t, b.original, 1, 1)
		counters(t, incoming, 0, 0)
	})
}

func TestIdentityDetachedPort(t *testing.T) {
	expected := map[string]int{"A": 0, "B": 1, "C": 0, "E": 1, "F": 1}
	for _, op := range operations {
		if op.name == "D" {
			continue
		}
		t.Run(op.name, func(t *testing.T) {
			b := newBinding()
			complete := op.admit(b)
			b.port.Target = nil
			if op.name == "A" {
				mustPanic(t, complete)
			} else {
				complete()
			}
			counters(t, b.original, 1, expected[op.name])
			b.port.Target = b.original
			counters(t, b.original, 1, expected[op.name])
			complete()
			counters(t, b.original, 1, expected[op.name]+1)
		})
	}
}

func unavailableEntry(t *testing.T, remove func(binding)) {
	t.Helper()
	for _, later := range []string{"no_later_input", "later_matching_key"} {
		t.Run(later, func(t *testing.T) {
			b := newBinding()
			complete := b.registry.D(key)
			remove(b)
			complete()
			counters(t, b.original, 1, 0)
			if later == "no_later_input" {
				return
			}
			incoming := &fixture.Account{Epoch: 8}
			if b.registry.Entries == nil {
				b.registry.Entries = make(map[string]*fixture.Account)
			}
			b.registry.Entries[key] = incoming
			counters(t, b.original, 1, 0)
			counters(t, incoming, 0, 0)
			complete()
			counters(t, b.original, 1, 0)
			counters(t, incoming, 0, 1)
		})
	}
}

func TestIdentityRegistryAbsent(t *testing.T) {
	unavailableEntry(t, func(b binding) { delete(b.registry.Entries, key) })
}

func TestIdentityRegistryNilEntry(t *testing.T) {
	unavailableEntry(t, func(b binding) { b.registry.Entries[key] = nil })
}

func TestIdentityRegistryNilMap(t *testing.T) {
	unavailableEntry(t, func(b binding) { b.registry.Entries = nil })
}

func TestIdentityRegistryMapReplacement(t *testing.T) {
	b := newBinding()
	incoming := &fixture.Account{Epoch: 8}
	unrelated := &fixture.Account{Epoch: 7}
	complete := b.registry.D(key)
	retired := b.registry.Entries
	b.registry.Entries = map[string]*fixture.Account{key: incoming, "other": unrelated}
	complete()
	counters(t, retired[key], 1, 0)
	counters(t, incoming, 0, 1)
	counters(t, unrelated, 0, 0)
}

func guardedOperations(t *testing.T, run func(*testing.T, operation, binding)) {
	t.Helper()
	for _, op := range operations {
		if op.name == "A" || op.name == "C" {
			t.Run(op.name, func(t *testing.T) { run(t, op, newBinding()) })
		}
	}
}

func TestIdentityEpochRestoration(t *testing.T) {
	guardedOperations(t, func(t *testing.T, op operation, b binding) {
		complete := op.admit(b)
		b.original.Epoch = 8
		complete()
		counters(t, b.original, 1, 0)
		b.original.Epoch = 7
		counters(t, b.original, 1, 0)
		complete()
		counters(t, b.original, 1, 1)
	})
}

func TestIdentityTargetRestoration(t *testing.T) {
	redirected := map[string]int{"A": 1, "C": 0}
	guardedOperations(t, func(t *testing.T, op operation, b binding) {
		incoming := &fixture.Account{Epoch: 7}
		complete := op.admit(b)
		b.port.Target = incoming
		complete()
		counters(t, b.original, 1, 0)
		counters(t, incoming, 0, redirected[op.name])
		b.port.Target = b.original
		counters(t, b.original, 1, 0)
		complete()
		counters(t, b.original, 1, 1)
		counters(t, incoming, 0, redirected[op.name])
	})
}

func TestIdentityAbandonedAndRepeated(t *testing.T) {
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		op.admit(b)
		counters(t, b.original, 1, 0)
		retained := op.admit(b)
		counters(t, b.original, 2, 0)
		retained()
		counters(t, b.original, 2, 1)
		retained()
		counters(t, b.original, 2, 2)
	})
}

func TestIdentityOverlappingAdmissions(t *testing.T) {
	expected := map[string][2]int{
		"A": {0, 2}, "B": {1, 1}, "C": {0, 1}, "D": {0, 2}, "E": {1, 1}, "F": {1, 1},
	}
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		incoming := &fixture.Account{Epoch: 7}
		older := op.admit(b)
		b.replace(op, incoming)
		newer := op.admit(b)
		counters(t, b.original, 1, 0)
		counters(t, incoming, 1, 0)
		newer()
		counters(t, b.original, 1, 0)
		counters(t, incoming, 1, 1)
		older()
		counters(t, b.original, 1, expected[op.name][0])
		counters(t, incoming, 1, expected[op.name][1])
	})
}

func TestIdentityInvalidAdmission(t *testing.T) {
	eachOperation(t, func(t *testing.T, op operation, b binding) {
		if op.name == "D" {
			for _, invalid := range []struct {
				name    string
				entries map[string]*fixture.Account
			}{
				{"missing", map[string]*fixture.Account{}},
				{"nil_entry", map[string]*fixture.Account{key: nil}},
				{"nil_map", nil},
			} {
				t.Run(invalid.name, func(t *testing.T) {
					b.registry.Entries = invalid.entries
					mustPanic(t, func() { op.admit(b) })
				})
			}
		} else {
			b.port.Target = nil
			mustPanic(t, func() { op.admit(b) })
		}
		counters(t, b.original, 0, 0)
	})
}

func TestIdentityValueCopy(t *testing.T) {
	b := newBinding()
	otherPort := *b.port
	incoming := &fixture.Account{Epoch: 8}
	complete := b.port.E()
	b.port.Target = incoming
	otherPort.Target = nil
	if otherPort.Target != nil {
		t.Fatal("other port remains bound")
	}
	complete()
	counters(t, b.original, 1, 1)
	counters(t, incoming, 0, 0)
}

func TestIdentityCapturedObjectAfterReset(t *testing.T) {
	b := newBinding()
	complete := b.port.B()
	b.original.Requests = 0
	b.original.Successes = 10
	complete()
	counters(t, b.original, 0, 11)
}

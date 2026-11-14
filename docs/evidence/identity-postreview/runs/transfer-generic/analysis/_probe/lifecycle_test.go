package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

func TestIdentityCallerDeparture(t *testing.T) {
	eachOperation(t, func(t *testing.T, op operation, _ binding) {
		for _, deliver := range []bool{false, true} {
			name := "no_later_input"
			if deliver {
				name = "later_completion"
			}
			t.Run(name, func(t *testing.T) {
				b := newBinding()
				// The delivery side retains the callback after admission returns.
				deliverySide := op.admit(b)
				incoming := &fixture.Account{Epoch: 7}
				b.replace(op, incoming)
				counters(t, b.original, 1, 0)
				counters(t, incoming, 0, 0)
				if deliver {
					deliverySide()
				}
				wantOriginal := map[string]int{"B": 1, "E": 1, "F": 1}
				wantIncoming := map[string]int{"A": 1, "D": 1}
				if !deliver {
					counters(t, b.original, 1, 0)
					counters(t, incoming, 0, 0)
					return
				}
				counters(t, b.original, 1, wantOriginal[op.name])
				counters(t, incoming, 0, wantIncoming[op.name])
			})
		}
	})
}

func TestIdentityMatchingAfterMismatch(t *testing.T) {
	t.Run("A", func(t *testing.T) {
		b := newBinding()
		incoming := &fixture.Account{Epoch: 8}
		complete := b.port.A()
		b.port.Target = incoming
		complete()
		counters(t, b.original, 1, 0)
		counters(t, incoming, 0, 0)
		incoming.Epoch = b.original.Epoch
		counters(t, incoming, 0, 0)
		complete()
		counters(t, b.original, 1, 0)
		counters(t, incoming, 0, 1)
	})
	t.Run("C", func(t *testing.T) {
		b := newBinding()
		incoming := &fixture.Account{Epoch: 7}
		complete := b.port.C()
		b.original.Epoch = 8
		b.port.Target = incoming
		complete()
		counters(t, b.original, 1, 0)
		counters(t, incoming, 0, 0)
		b.port.Target = b.original
		complete()
		counters(t, b.original, 1, 0)
		b.original.Epoch = 7
		counters(t, b.original, 1, 0)
		complete()
		counters(t, b.original, 1, 1)
		counters(t, incoming, 0, 0)
	})
}

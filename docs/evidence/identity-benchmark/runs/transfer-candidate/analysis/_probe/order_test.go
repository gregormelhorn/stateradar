package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

func TestIdentityDepartureWithoutDelivery(t *testing.T) {
	for _, api := range []string{"A", "B", "C", "D", "E", "F"} {
		t.Run(api, func(t *testing.T) {
			a := &fixture.Account{Epoch: 7}
			p := &fixture.Port{Target: a}
			r := &fixture.Registry{Entries: map[string]*fixture.Account{"k": a}}
			switch api {
			case "A":
				p.A()
			case "B":
				p.B()
			case "C":
				p.C()
			case "D":
				r.D("k")
			case "E":
				p.E()
			case "F":
				fixture.F(p)
			}
			p.Target = nil
			delete(r.Entries, "k")
			counters(t, a, 1, 0)
		})
	}
}

func TestIdentityDeliveryAcrossReplacement(t *testing.T) {
	t.Run("A matching replacement", func(t *testing.T) {
		a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.A()
		done()
		counters(t, a, 1, 1)
		p.Target = b
		done()
		counters(t, a, 1, 1)
		counters(t, b, 0, 1)
	})
	t.Run("C matching replacement", func(t *testing.T) {
		a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.C()
		done()
		counters(t, a, 1, 1)
		p.Target = b
		done()
		counters(t, a, 1, 1)
		counters(t, b, 0, 0)
	})
	t.Run("D replacement at key", func(t *testing.T) {
		a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 8}
		r := &fixture.Registry{Entries: map[string]*fixture.Account{"k": a}}
		done := r.D("k")
		done()
		counters(t, a, 1, 1)
		r.Entries["k"] = b
		done()
		counters(t, a, 1, 1)
		counters(t, b, 0, 1)
	})
}

package identityfixture_test

import (
	"testing"

	fixture "identityfixture"
)

func counters(t *testing.T, a *fixture.Account, requests, successes int) {
	t.Helper()
	if a.Requests != requests || a.Successes != successes {
		t.Fatalf("account counters = (%d, %d), want (%d, %d)", a.Requests, a.Successes, requests, successes)
	}
}

func panics(t *testing.T, call func()) {
	t.Helper()
	defer func() {
		if recover() == nil {
			t.Fatal("operation returned without panicking")
		}
	}()
	call()
}

func TestIdentityAEpochAndTarget(t *testing.T) {
	for _, scenario := range []string{"unchanged", "matching replacement", "different epoch replacement", "epoch change and restoration", "cleared"} {
		t.Run(scenario, func(t *testing.T) {
			a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 7}
			p := &fixture.Port{Target: a}
			done := p.A()
			counters(t, a, 1, 0)
			switch scenario {
			case "unchanged":
				done()
				counters(t, a, 1, 1)
			case "matching replacement":
				p.Target = b
				done()
				counters(t, a, 1, 0)
				counters(t, b, 0, 1)
			case "different epoch replacement":
				b.Epoch = 8
				p.Target = b
				done()
				counters(t, a, 1, 0)
				counters(t, b, 0, 0)
			case "epoch change and restoration":
				a.Epoch = 8
				done()
				counters(t, a, 1, 0)
				a.Epoch = 7
				done()
				counters(t, a, 1, 1)
			case "cleared":
				p.Target = nil
				panics(t, done)
				counters(t, a, 1, 0)
				p.Target = a
				done()
				counters(t, a, 1, 1)
			}
		})
	}
}

func TestIdentityAPortIdentity(t *testing.T) {
	t.Run("caller rebind and copy", func(t *testing.T) {
		a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		copyPort := *p
		done := p.A()
		p = &copyPort
		p.Target = b
		done()
		counters(t, a, 1, 1)
		counters(t, b, 0, 0)
	})
	t.Run("overwrite original port and copy account", func(t *testing.T) {
		a := &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.A()
		copyAccount := *a
		*p = fixture.Port{Target: &copyAccount}
		done()
		counters(t, a, 1, 0)
		counters(t, &copyAccount, 1, 1)
	})
}

func TestIdentityCapturedAccounts(t *testing.T) {
	methods := []struct {
		name  string
		admit func(*fixture.Port) func()
	}{
		{"B", (*fixture.Port).B},
		{"E", (*fixture.Port).E},
		{"F", fixture.F},
	}
	for _, method := range methods {
		t.Run(method.name, func(t *testing.T) {
			t.Run("retarget and epoch change", func(t *testing.T) {
				a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 8}
				p := &fixture.Port{Target: a}
				done := method.admit(p)
				counters(t, a, 1, 0)
				p.Target = b
				a.Epoch = 9
				done()
				counters(t, a, 1, 1)
				counters(t, b, 0, 0)
			})
			t.Run("cleared port", func(t *testing.T) {
				a := &fixture.Account{Epoch: 7}
				p := &fixture.Port{Target: a}
				done := method.admit(p)
				p.Target = nil
				done()
				counters(t, a, 1, 1)
			})
		})
	}
}

func TestIdentityCIdentityAndEpoch(t *testing.T) {
	t.Run("unchanged", func(t *testing.T) {
		a := &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.C()
		counters(t, a, 1, 0)
		done()
		counters(t, a, 1, 1)
	})
	t.Run("equal account copy and restored pointer", func(t *testing.T) {
		a := &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.C()
		copyAccount := *a
		p.Target = &copyAccount
		done()
		counters(t, a, 1, 0)
		counters(t, &copyAccount, 1, 0)
		p.Target = a
		done()
		counters(t, a, 1, 1)
	})
	t.Run("same account epoch change and restoration", func(t *testing.T) {
		a := &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.C()
		a.Epoch = 8
		done()
		counters(t, a, 1, 0)
		a.Epoch = 7
		done()
		counters(t, a, 1, 1)
	})
	t.Run("cleared port", func(t *testing.T) {
		a := &fixture.Account{Epoch: 7}
		p := &fixture.Port{Target: a}
		done := p.C()
		p.Target = nil
		done()
		counters(t, a, 1, 0)
	})
}

func TestIdentityDRegistryAndKey(t *testing.T) {
	for _, scenario := range []string{"unchanged", "entry replacement", "delete", "nil entry", "nil map", "reinsert", "map replacement", "caller rebind", "copy shares map", "caller reassigns key"} {
		t.Run(scenario, func(t *testing.T) {
			a, b := &fixture.Account{Epoch: 7}, &fixture.Account{Epoch: 8}
			r := &fixture.Registry{Entries: map[string]*fixture.Account{"k": a, "j": b}}
			copyRegistry := *r
			key := "k"
			done := r.D(key)
			counters(t, a, 1, 0)
			wantA, wantB := 0, 0
			switch scenario {
			case "unchanged":
				wantA = 1
			case "entry replacement":
				r.Entries["k"] = b
				wantB = 1
			case "delete":
				delete(r.Entries, "k")
			case "nil entry":
				r.Entries["k"] = nil
			case "nil map":
				r.Entries = nil
			case "reinsert":
				delete(r.Entries, "k")
				done()
				counters(t, a, 1, 0)
				counters(t, b, 0, 0)
				r.Entries["k"] = b
				wantB = 1
			case "map replacement":
				r.Entries = map[string]*fixture.Account{"k": b}
				if copyRegistry.Entries["k"] != a {
					t.Fatal("old map entry changed")
				}
				wantB = 1
			case "caller rebind":
				r = &copyRegistry
				r.Entries = map[string]*fixture.Account{"k": b}
				wantA = 1
			case "copy shares map":
				copyRegistry.Entries["k"] = b
				wantB = 1
			case "caller reassigns key":
				key = "j"
				if r.Entries[key] != b {
					t.Fatal("replacement key did not select b in caller")
				}
				wantA = 1
			}
			done()
			counters(t, a, 1, wantA)
			counters(t, b, 0, wantB)
		})
	}
}

func TestIdentityAdmissionAndRepeat(t *testing.T) {
	for _, api := range []string{"A", "B", "C", "D", "E", "F"} {
		t.Run(api, func(t *testing.T) {
			a := &fixture.Account{Epoch: 7}
			p := &fixture.Port{Target: a}
			r := &fixture.Registry{Entries: map[string]*fixture.Account{"k": a}}
			var done func()
			switch api {
			case "A":
				done = p.A()
			case "B":
				done = p.B()
			case "C":
				done = p.C()
			case "D":
				done = r.D("k")
			case "E":
				done = p.E()
			case "F":
				done = fixture.F(p)
			}
			counters(t, a, 1, 0)
			done()
			counters(t, a, 1, 1)
			done()
			counters(t, a, 1, 2)
		})
	}
}

func TestIdentityNilAdmission(t *testing.T) {
	p := &fixture.Port{}
	for name, call := range map[string]func(){
		"A":            func() { p.A() },
		"B":            func() { p.B() },
		"C":            func() { p.C() },
		"E":            func() { p.E() },
		"F":            func() { fixture.F(p) },
		"F nil port":   func() { fixture.F(nil) },
		"D absent key": func() { (&fixture.Registry{Entries: map[string]*fixture.Account{}}).D("k") },
		"D nil entry":  func() { (&fixture.Registry{Entries: map[string]*fixture.Account{"k": nil}}).D("k") },
		"D nil map":    func() { (&fixture.Registry{}).D("k") },
	} {
		t.Run(name, func(t *testing.T) {
			panics(t, call)
		})
	}
}

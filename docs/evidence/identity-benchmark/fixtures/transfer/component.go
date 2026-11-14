package identityfixture

type Account struct { Requests, Successes, Epoch int }
type Port struct { Target *Account }
type Registry struct { Entries map[string]*Account }

func (p *Port) A() func() {
 p.Target.Requests++
 epoch := p.Target.Epoch
 return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }
}
func (p *Port) B() func() {
 target := p.Target
 target.Requests++
 return func() { target.Successes++ }
}
func (p *Port) C() func() {
 target, epoch := p.Target, p.Target.Epoch
 target.Requests++
 return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }
}
func (r *Registry) D(key string) func() {
 r.Entries[key].Requests++
 return func() { if target := r.Entries[key]; target != nil { target.Successes++ } }
}
func (p Port) E() func() {
 p.Target.Requests++
 return func() { p.Target.Successes++ }
}
func F(p *Port) func() {
 target := p.Target
 target.Requests++
 return func() { target.Successes++ }
}

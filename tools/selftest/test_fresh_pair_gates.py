import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresh_pair_gates import tally,allow_blind,route_policy,enforce_cap,live_budget
class GateTests(unittest.TestCase):
 def setUp(self):self.usage={'input_tokens':1000,'cached_input_tokens':0,'output_tokens':100}
 def test_cost_includes_all_parts(self):
  n=tally(.1,{'usage':self.usage},[{'status':'settled','amount_microdollars':2000}],[{'usage':self.usage,'complete':True}]);self.assertGreater(n,.1)
 def test_unknown_prior_or_blind_fails(self):
  for prior,blind in ((None,[]),(.1,[{'usage':None,'complete':False}])):
   with self.assertRaisesRegex(ValueError,'unknown'):tally(prior,{'usage':self.usage},[],blind)
 def test_reserved_provider_fails(self):
  with self.assertRaisesRegex(ValueError,'unsettled'):tally(.1,{'usage':self.usage},[{'status':'reserved','amount_microdollars':1}],[])
 def test_blind_requires_exact_output_and_package(self):
  out='domain-analysis/lruCache/part-b-blind.md'
  allow_blind(['blind','--requirements','README.md','--contracts','contracts.md','--output',out],out)
  for args in (['blind','--output','other'],['blind','--output',out,'--output',out],['blind','--output',out,'--package-only']):
   with self.assertRaises(ValueError):allow_blind(args,out)
class PolicyTests(unittest.TestCase):
 def test_direct_provider_calls_refused(self):
  for command in ('flash','jev','draft-verify','jev-batch'):
   self.assertEqual(route_policy('direct',command,False),'deny')
 def test_direct_blind_dispatch_and_package_only(self):
  self.assertEqual(route_policy('direct','blind',True),'package')
  self.assertEqual(route_policy('direct','blind',False),'blind')
 def test_routed_uses_normal_tool(self):self.assertEqual(route_policy('routed','jev-batch',False),'normal')
class CapTests(unittest.TestCase):
 def test_cap_stops_at_and_above(self):
  for amount in (5,5.1):
   with self.assertRaisesRegex(ValueError,'budget reached'):enforce_cap(amount,5)
 def test_under_cap_allowed(self):enforce_cap(4.99,5)
class LiveBudgetTests(unittest.TestCase):
 def test_unreported_controller_cannot_continue(self):
  with self.assertRaisesRegex(ValueError,'unknown controller'):live_budget(.1,None,[],0,181,5)
 def test_reserved_provider_counts_toward_cap(self):
  with self.assertRaisesRegex(ValueError,'budget reached'):live_budget(4.0,None,[{'amount_microdollars':1100000,'status':'reserved'}],0,10,5)
 def test_controller_usage_counts_toward_cap(self):
  usage={'input_tokens':1000000,'cached_input_tokens':0,'output_tokens':1000000}
  with self.assertRaisesRegex(ValueError,'budget reached'):live_budget(.1,usage,[],0,10,5)
if __name__=='__main__':unittest.main()

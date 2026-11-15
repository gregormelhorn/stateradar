import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresh_pair_smoke_check import verify
class SmokeTest(unittest.TestCase):
 def events(self):
  def event(argv,data):return {'type':'item.completed','item':{'type':'mcp_tool_call','server':'pilot','tool':'command','arguments':{'argv':argv},'result':{'content':[{'type':'text','text':json.dumps(data)}]}}}
  return [event(['cat','go.mod'],{'exit_code':0,'stdout':'module github.com/hashicorp/golang-lru/v2\n'}),event(['python3','../pack/tools/local_models.py','--ledger','../routing.sqlite','jev'],{'exit_code':2,'stderr':'Model providers are unavailable in the direct arm.'})]
 def test_success(self):verify('github.com/hashicorp/golang-lru/v2',self.events())
 def test_missing_denial(self):
  with self.assertRaisesRegex(ValueError,'provider refusal'):verify('github.com/hashicorp/golang-lru/v2',self.events()[:1])
 def test_missing_read(self):
  with self.assertRaisesRegex(ValueError,'module read'):verify('github.com/hashicorp/golang-lru/v2',self.events()[1:])
 def test_refuses_other_tool(self):
  events=self.events()+[{'type':'item.completed','item':{'type':'web_search'}}]
  with self.assertRaisesRegex(ValueError,'unexpected tool'):verify('github.com/hashicorp/golang-lru/v2',events)
if __name__=='__main__':unittest.main()

"""Validate actual MCP smoke events, including direct-provider refusal."""
import json

def verify(final,events):
 if 'github.com/hashicorp/golang-lru/v2' not in final:raise ValueError('module missing from final')
 seen_read=False;seen_denial=False
 for event in events:
  item=event.get('item',{});kind=item.get('type')
  if kind in ('command_execution','web_search','file_change'):raise ValueError('unexpected tool')
  if kind!='mcp_tool_call' or event.get('type')!='item.completed':continue
  if item.get('server')!='pilot' or item.get('tool')!='command':raise ValueError('unexpected tool')
  argv=item.get('arguments',{}).get('argv',[]);content=item.get('result',{}).get('content',[])
  if not content:raise ValueError('missing tool result')
  result=json.loads(content[0]['text'])
  if argv==['cat','go.mod'] and result.get('exit_code')==0 and 'module github.com/hashicorp/golang-lru/v2' in result.get('stdout',''):seen_read=True
  if len(argv)>=5 and argv[0]=='python3' and argv[4]=='jev' and result.get('exit_code')==2 and 'Model providers are unavailable' in result.get('stderr',''):seen_denial=True
 if not seen_read:raise ValueError('module read missing')
 if not seen_denial:raise ValueError('provider refusal missing')
 return True

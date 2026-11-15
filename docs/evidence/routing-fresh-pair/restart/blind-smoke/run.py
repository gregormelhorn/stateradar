import os,shutil,sys
from pathlib import Path
sys.path.insert(0,'/tmp/stateradar-routing-fresh-pilot/tools')
import run_fresh_routing_pair as pair
root=Path('/tmp/stateradar-blind-restart-smoke/direct').resolve()
a=root/'pool/domain-analysis/lruCache';a.mkdir(parents=True,exist_ok=True)
(a/'event-catalogue.md').write_text('''<!-- event-ids: E01 -->
# Fictional single-button lamp catalogue
E01: Press is an external request from a user to switch the lamp on. The request contains no payload. The lamp has only the states Off and On. Each press is delivered once. This fictional example is exclusively for testing the blind dispatch path and is not related to any source repository.\n''')
(a/'requirements.md').write_text('''# Fictional lamp requirements
The lamp starts in Off. When Press arrives in Off, the lamp transitions to On and emits a light-on effect. When Press arrives in On, the lamp stays in On and emits no additional effect. This fictional requirement fully specifies this one event and is used solely for a short technical smoke test.\n''')
(a/'contracts.txt').write_text('''# Fictional event contract
Press is an external event with no parameters. The caller sends Press at most once per interaction. The event is delivered to the lamp in the order it is issued. The lamp is a single component with exactly two states: Off and On. The event contract has no additional error cases or unspecified payload fields.\n''')
pair.prompt=lambda pack,arm: '''Use only the pilot command tool. A fictional catalogue already exists at domain-analysis/lruCache/event-catalogue.md; its requirements and contracts are requirements.md and contracts.txt in the same directory. Do not read source code or inspect any other repository content. First assemble a blind package using exactly this command array: ["python3","../pack/tools/local_models.py","--ledger","../routing.sqlite","blind","domain-analysis/lruCache","--repo",".","--requirements","domain-analysis/lruCache/requirements.md","--contracts","domain-analysis/lruCache/contracts.txt","--output","domain-analysis/lruCache/part-b-blind.md","--package-only"]. Read the entire generated domain-analysis/lruCache/part-b-blind.package.md using the command tool. Then run the same command without --package-only, keeping --output and its value last. Do not write or edit the blind output yourself. Report the command's result and stop. This is only a tiny fictional technical smoke test.\n'''
report,complete=pair.run_arm(root,'direct',0.0,Path(sys.executable).absolute(),shutil.which(os.environ['CODEX_APP_RUNTIME_CLI_PATH']),pair.ROOT/'tools/fresh_pair_server.py')
print('SMOKE RUN REPORT',report,'artifact_gates',complete,flush=True)

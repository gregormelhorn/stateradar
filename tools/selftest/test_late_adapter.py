"""The real adapter refuses exit-zero tools with no discovered Go tests."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
FIXTURE=ROOT/'examples/grpc-addrconn/late-completion'

class Adapter(unittest.TestCase):
    def test_empty_go_execution_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();shutil.copytree(FIXTURE,root/'late')
            shutil.copyfile(ROOT/'tools/late_completion.py',root/'late/late_completion.py')
            (root/'clientconn.go').write_text('''func (ac *addrConn) resetTransport() {
transport.NewClientTransport(connectCtx, ac.cc.ctx, target, copts, onPrefaceReceipt, onGoAway, onClose)
newTr, err := ac.createTransport(addr, copts, connectDeadline, reconnect, prefaceReceived)
healthCheckConfig := ac.cc.healthCheckConfig()
\t\t\tac.mu.Lock()
\t\t\treqHandshake := ac.dopts.reqHandshake
func (cc *ClientConn) handleSubConnStateChange(sc balancer.SubConn, s connectivity.State) {
''')
            (root/'bin').mkdir();fake=root/'bin/go'
            fake.write_text('#!/usr/bin/env python3\nprint("PASS (no actual tests)")\n');fake.chmod(0o755)
            run=subprocess.run([sys.executable,root/'late/run.py','--analysis',root/'late'],capture_output=True,text=True,
                env={**os.environ,'PATH':str(root/'bin')+os.pathsep+os.environ['PATH']})
            self.assertEqual(run.returncode,2)
            self.assertIn('BLOCKED: incomplete/failed adapter execution',run.stdout+run.stderr)
            self.assertNotIn('CELL SUITE:',run.stdout)

if __name__=='__main__':unittest.main()

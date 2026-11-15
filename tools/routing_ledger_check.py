"""Compare saved ledger summaries with the persistent read-only ledger."""
import sqlite3
from contextlib import closing
from pathlib import Path

def verify(path,summary):
 path=Path(path)
 if not path.is_file():raise ValueError('ledger missing')
 try:
  with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
   limits=db.execute('SELECT limit_amount FROM config').fetchall()
   rows=db.execute('SELECT id,provider,amount,status FROM calls ORDER BY id').fetchall()
  if len(limits)!=1:raise ValueError('ledger mismatch: invalid config')
  calls=[{'id':r[0],'provider':r[1],'amount_microdollars':r[2],'status':r[3]} for r in rows]
  actual={'limit_microdollars':limits[0][0],'total_microdollars':sum(r[2] for r in rows),'calls':calls}
  if actual!=summary:raise ValueError('ledger mismatch: summary differs')
 except sqlite3.Error as exc:raise ValueError('ledger mismatch: '+str(exc)) from exc

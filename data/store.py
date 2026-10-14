import sys
sys.path.insert(0,'lib')
from common import *
import sqlite3

def main():
    args=sys.argv[1:]
    if not args or args[0] not in ('init','upsert','list','get'): return 2
    folder=ROOT/'data/evidence'; folder.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(folder/'index.sqlite3')
    db.executescript('CREATE TABLE IF NOT EXISTS versions(item TEXT, version TEXT, record TEXT, PRIMARY KEY(item,version)); CREATE TABLE IF NOT EXISTS latest(item TEXT PRIMARY KEY, version TEXT); CREATE TABLE IF NOT EXISTS observations(item TEXT,version TEXT,run TEXT, UNIQUE(item,version,run));')
    cmd=args[0]
    if cmd=='upsert':
        if len(args)!=2: return 2
        stage=Stage(args[1],'store'); values=rows(); stage.input=len(values)
        for item in values:
            i,v=item['item_id'],item['version_id']; old=db.execute('SELECT version FROM latest WHERE item=?',(i,)).fetchone()
            exists=db.execute('SELECT 1 FROM versions WHERE item=? AND version=?',(i,v)).fetchone()
            change='unchanged' if old and old[0]==v else ('new' if old is None else 'changed')
            if not exists: db.execute('INSERT INTO versions VALUES(?,?,?)',(i,v,json.dumps(item)))
            db.execute('INSERT OR REPLACE INTO latest VALUES(?,?)',(i,v)); db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?)',(i,v,args[1]))
            emit({'item_id':i,'version_id':v,'change':change}); stage.output+=1
        db.commit(); stage.finish()
    elif cmd=='list':
        for (record,) in db.execute('SELECT v.record FROM versions v JOIN latest l ON v.item=l.item AND v.version=l.version ORDER BY v.item'): emit(json.loads(record))
    elif cmd=='get':
        if len(args) not in (2,3): return 2
        if len(args)==3: row=db.execute('SELECT record FROM versions WHERE item=? AND version=?',(args[1],args[2])).fetchone()
        else: row=db.execute('SELECT v.record FROM versions v JOIN latest l ON v.item=l.item AND v.version=l.version WHERE v.item=?',(args[1],)).fetchone()
        if not row: print('Item or version not found',file=sys.stderr); return 1
        emit(json.loads(row[0]))
    db.commit(); db.close(); return 0
invoke(main)

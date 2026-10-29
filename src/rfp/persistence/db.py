"""SQLite owns immutable snapshots, call accounting, leases and atomic results."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import time
from rfp.contracts import digest, validate_criteria

SEEDS = [
    (1, 'Technical Capability', 'Architecture, integrations, scalability and technical fit.', '30'),
    (2, 'Implementation Plan', 'Timeline, milestones, staffing and risk plan.', '20'),
    (3, 'Commercial Value', 'Pricing clarity, total cost and explicit assumptions.', '20'),
    (4, 'Security & Compliance', 'Access controls, certifications, privacy, recovery and auditability.', '20'),
    (5, 'Support & Experience', 'Support commitments, relevant projects and references.', '10'),
]
TARGETS = {1: '7', 2: '7', 3: '6', 4: '8', 5: '7'}


def now():
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'rfp.sqlite'
        self.artifacts = self.directory / 'artifacts'
        self.artifacts.mkdir(exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            with con:
                yield con
        finally:
            con.close()

    def initialize(self):
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS evaluation_criteria (
              criterion_id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
              weight TEXT NOT NULL, max_score TEXT NOT NULL, is_active INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS rfp_runs (
              rfp_run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL,
              owner_hash TEXT NOT NULL, input_fingerprint TEXT NOT NULL, provider_json TEXT NOT NULL,
              criteria_json TEXT, criteria_hash TEXT, baseline_json TEXT, export_json TEXT,
              result_hash TEXT, error_json TEXT, lease_token TEXT, lease_until REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS run_suppliers (
              rfp_run_id TEXT NOT NULL REFERENCES rfp_runs, supplier_id TEXT NOT NULL,
              supplier_name TEXT NOT NULL, submission_date TEXT NOT NULL, experience_rating TEXT NOT NULL,
              input_json TEXT NOT NULL, PRIMARY KEY(rfp_run_id,supplier_id));
            CREATE TABLE IF NOT EXISTS supplier_evaluations (
              rfp_run_id TEXT NOT NULL REFERENCES rfp_runs, supplier_id TEXT NOT NULL,
              attempts INTEGER DEFAULT 0, normalized_json TEXT,
              PRIMARY KEY(rfp_run_id,supplier_id));
            CREATE TABLE IF NOT EXISTS model_responses (
              rfp_run_id TEXT NOT NULL, supplier_id TEXT NOT NULL, attempt INTEGER NOT NULL,
              prompt_hash TEXT NOT NULL, response_json TEXT NOT NULL,
              PRIMARY KEY(rfp_run_id,supplier_id,attempt),
              FOREIGN KEY(rfp_run_id,supplier_id) REFERENCES supplier_evaluations);
            CREATE TABLE IF NOT EXISTS supplier_results (
              rfp_run_id TEXT NOT NULL REFERENCES rfp_runs, supplier_id TEXT NOT NULL,
              supplier_name TEXT NOT NULL, submission_date TEXT NOT NULL, experience_rating TEXT NOT NULL,
              absolute_score REAL NOT NULL, ppi REAL NOT NULL, final_rank INTEGER NOT NULL,
              result_json TEXT NOT NULL, PRIMARY KEY(rfp_run_id,supplier_id),
              UNIQUE(rfp_run_id,final_rank));
            CREATE TABLE IF NOT EXISTS run_events (
              event_id TEXT PRIMARY KEY, rfp_run_id TEXT REFERENCES rfp_runs,
              node_id TEXT NOT NULL, node_name TEXT NOT NULL, supplier_id TEXT,
              created_at TEXT NOT NULL, outcome TEXT NOT NULL);
            ''')
            c.executemany('INSERT OR IGNORE INTO evaluation_criteria VALUES(?,?,?,?,?,1)',
                          [(i,n,d,w,'10') for i,n,d,w in SEEDS])

    def criteria(self, active=True):
        with self.connect() as c:
            rows = c.execute('SELECT * FROM evaluation_criteria ORDER BY criterion_id').fetchall()
        return [dict(row) for row in rows if not active or row['is_active']]

    def update_criteria(self, rows):
        validate_criteria(rows)
        with self.connect() as c:
            for row in rows:
                c.execute('UPDATE evaluation_criteria SET weight=?,is_active=? WHERE criterion_id=?',
                          (str(row['weight']), int(row['is_active']), int(row['criterion_id'])))

    def create_run(self, run_id, owner, suppliers, provider):
        with self.connect() as c:
            c.execute('INSERT INTO rfp_runs(rfp_run_id,created_at,status,owner_hash,input_fingerprint,provider_json) VALUES(?,?,?,?,?,?)',
                      (run_id, now(), 'running', owner, digest(suppliers), json.dumps(provider)))
            for s in suppliers:
                c.execute('INSERT INTO run_suppliers VALUES(?,?,?,?,?,?)',
                          (run_id,s['supplier_id'],s['supplier_name'],s['submission_date'],s['experience_rating'],json.dumps(s)))
                c.execute('INSERT INTO supplier_evaluations(rfp_run_id,supplier_id) VALUES(?,?)',(run_id,s['supplier_id']))

    def run(self, run_id, owner):
        with self.connect() as c:
            row = c.execute('SELECT * FROM rfp_runs WHERE rfp_run_id=? AND owner_hash=?',(run_id,owner)).fetchone()
        if not row:
            raise PermissionError('Run not available in this session.')
        return dict(row)

    def freeze(self, run_id, owner):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row = c.execute('SELECT * FROM rfp_runs WHERE rfp_run_id=? AND owner_hash=?',(run_id,owner)).fetchone()
            if not row:
                raise PermissionError('Run not available.')
            if row['criteria_json']:
                return json.loads(row['criteria_json']), json.loads(row['baseline_json'])
            criteria = validate_criteria([dict(r) for r in c.execute('SELECT * FROM evaluation_criteria')])
            baseline = {'version':'illustrative-v1','source_type':'illustrative',
                        'label':'Illustrative classroom baseline - not measured industry averages',
                        'targets':{str(x['criterion_id']):{'score':TARGETS.get(x['criterion_id']), 'max_score':'10'} for x in criteria}}
            c.execute('UPDATE rfp_runs SET criteria_json=?,criteria_hash=?,baseline_json=? WHERE rfp_run_id=?',
                      (json.dumps(criteria),digest(criteria),json.dumps(baseline),run_id))
        return criteria,baseline

    def claim(self, run_id, owner, token):
        with self.connect() as c:
            cur=c.execute("UPDATE rfp_runs SET lease_token=?,lease_until=? WHERE rfp_run_id=? AND owner_hash=? AND status='running' AND (lease_until<? OR lease_token=?)",
                          (token,time.time()+180,run_id,owner,time.time(),token))
            if cur.rowcount!=1:
                raise ValueError('Run is already executing or is terminal. Retry recovery after its lease expires.')

    def heartbeat(self, run_id, token):
        with self.connect() as c:
            cur=c.execute('UPDATE rfp_runs SET lease_until=? WHERE rfp_run_id=? AND lease_token=?',(time.time()+180,run_id,token))
            if cur.rowcount!=1:
                raise ValueError('Run execution claim lost.')

    def release(self, run_id, token):
        with self.connect() as c:
            c.execute('UPDATE rfp_runs SET lease_until=0,lease_token=NULL WHERE rfp_run_id=? AND lease_token=?',(run_id,token))

    def staged(self, run_id, supplier_id):
        with self.connect() as c:
            row=c.execute('SELECT * FROM supplier_evaluations WHERE rfp_run_id=? AND supplier_id=?',(run_id,supplier_id)).fetchone()
        return dict(row)

    def reserve_call(self, run_id, supplier_id):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT attempts FROM supplier_evaluations WHERE rfp_run_id=? AND supplier_id=?',(run_id,supplier_id)).fetchone()
            if row['attempts']>=3:
                raise ValueError('Model call budget exhausted for this supplier.')
            attempt=row['attempts']+1
            c.execute('UPDATE supplier_evaluations SET attempts=? WHERE rfp_run_id=? AND supplier_id=?',(attempt,run_id,supplier_id))
            return attempt

    def response(self, run_id, supplier_id, prompt_hash):
        with self.connect() as c:
            row=c.execute('SELECT response_json FROM model_responses WHERE rfp_run_id=? AND supplier_id=? AND prompt_hash=? ORDER BY attempt DESC LIMIT 1',
                          (run_id,supplier_id,prompt_hash)).fetchone()
        return json.loads(row[0]) if row else None

    def save_response(self, run_id, supplier_id, attempt, prompt_hash, response):
        with self.connect() as c:
            c.execute('INSERT INTO model_responses VALUES(?,?,?,?,?)',(run_id,supplier_id,attempt,prompt_hash,json.dumps(response)))

    def stage(self, run_id, supplier_id, card):
        with self.connect() as c:
            c.execute('UPDATE supplier_evaluations SET normalized_json=? WHERE rfp_run_id=? AND supplier_id=?',(json.dumps(card),run_id,supplier_id))

    def event(self, run_id, node_id, name, supplier_id, occurrence, outcome='ok'):
        with self.connect() as c:
            c.execute('INSERT OR IGNORE INTO run_events VALUES(?,?,?,?,?,?,?)',
                      (f'{run_id}:{node_id}:{supplier_id}:{occurrence}',run_id,node_id,name,supplier_id,now(),outcome))

    def events(self, run_id, owner):
        self.run(run_id,owner)
        with self.connect() as c:
            return [dict(row) for row in c.execute('SELECT node_id,node_name,supplier_id,created_at,outcome FROM run_events WHERE rfp_run_id=? ORDER BY created_at,event_id',(run_id,))]

    def complete(self, run_id, owner, result):
        encoded=json.dumps(result,sort_keys=True,ensure_ascii=False)
        result_hash=digest(result)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            run=c.execute('SELECT * FROM rfp_runs WHERE rfp_run_id=? AND owner_hash=?',(run_id,owner)).fetchone()
            if not run:
                raise PermissionError('Run not available.')
            if run['status']=='completed':
                if run['result_hash']!=result_hash:
                    raise ValueError('Completed result conflicts with attempted save.')
                return
            count=c.execute('SELECT COUNT(*) FROM run_suppliers WHERE rfp_run_id=?',(run_id,)).fetchone()[0]
            if len(result['suppliers'])!=count:
                raise ValueError('Cannot save partial results as completed.')
            for s in result['suppliers']:
                c.execute('INSERT INTO supplier_results VALUES(?,?,?,?,?,?,?,?,?)',
                          (run_id,s['supplier_id'],s['supplier_name'],s['submission_date'],s['experience_rating'],
                           float(s['absolute_score']),float(s['ppi']),s['final_rank'],json.dumps(s)))
            c.execute("UPDATE rfp_runs SET status='completed',export_json=?,result_hash=? WHERE rfp_run_id=?",(encoded,result_hash,run_id))

    def fail(self, run_id, error):
        with self.connect() as c:
            c.execute("UPDATE rfp_runs SET status='failed',error_json=? WHERE rfp_run_id=? AND status!='completed'",(json.dumps(error),run_id))

from pathlib import Path
import pytest
from rfp.persistence.db import Repository
from rfp.services.runs import prepare_run,execute_run
from rfp.clients.llm import ProviderFailure
from test_core import FakeClient,prepared,PROVIDER,ROOT


def test_five_supplier_batch_is_supported(tmp_path):
    files=[(p.name,p.read_bytes()) for p in sorted((ROOT/'fixtures/proposals').glob('*.pdf'))]
    files.append(('fifth_vendor.pdf',files[0][1]+b'\n% Different synthetic fixture version\n'))
    metadata=[{'supplier_name':f'Vendor {i}','submission_date':'2026-10-12','experience_rating':'5'} for i in range(5)]
    repo=Repository(tmp_path);run_id=prepare_run(repo,'owner',files,metadata,PROVIDER)
    result=execute_run(repo,run_id,'owner',FakeClient())
    assert len(result['suppliers'])==5


def test_transport_retry_is_bounded_and_visible(tmp_path,monkeypatch):
    import rfp.graph.build
    monkeypatch.setattr(rfp.graph.build,'sleep',lambda n:None)
    class Transient(FakeClient):
        def evaluate(self,prompt):
            if self.calls==0:
                self.calls+=1
                raise ProviderFailure('Transient test failure',retryable=True)
            return super().evaluate(prompt)
    repo=Repository(tmp_path);run_id=prepared(repo);client=Transient()
    result=execute_run(repo,run_id,'owner',client)
    assert client.calls==5
    assert any(e['node_id']=='F14' for e in result['events'])

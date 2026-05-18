def test_end_to_end_audit(client, tmp_path):
    # client is a test FastAPI client fixture
    sample = tmp_path / "sample.csv"
    # generate or copy sample.csv into sample
    resp = client.post("/ingest", files={"file": open(sample,'rb')})
    assert resp.status_code == 200
    job_id = resp.json()['job_id']
    run = client.post(f"/run_audit/{job_id}")
    assert run.status_code == 200
    assert 'fairness' in run.json()
    assert 'reliability' in run.json()

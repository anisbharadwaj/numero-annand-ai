def test_disparate_impact():
    import pandas as pd
    from backend.metrics.fairness import disparate_impact
    df = pd.DataFrame({"group":["A","A","B","B"], "out":[1,0,1,0]})
    di = disparate_impact(df, "group", "out", privileged_value="A")
    assert di is not None

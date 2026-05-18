from backend.utils.protected_edge_tabs import sanitize_text, safe_summary, edge_all_open_tabs

def test_sanitize_text_removes_tags():
    raw = "<tag>Hello  World</tag>"
    assert sanitize_text(raw) == "Hello World"

def test_safe_summary_contains_domain_and_counts():
    summary = safe_summary(edge_all_open_tabs)
    assert "current_tab" in summary
    assert isinstance(summary["background_tab_count"], int)
    assert isinstance(summary["background_domains"], list)

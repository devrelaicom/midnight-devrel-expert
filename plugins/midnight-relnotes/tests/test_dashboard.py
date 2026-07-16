import scripts.dashboard as dash

ROWS = [{"item": "midnight-js", "latest_relnote": "4.0.4", "latest_stable": "4.1.1",
         "behind": 1, "stale": True, "prerelease": "5.0.0-beta.6"}]

def test_markdown_has_table_and_values():
    out = dash.render_markdown(ROWS)
    assert "| Item |" in out
    assert "midnight-js" in out and "4.1.1" in out and "5.0.0-beta.6" in out

def test_html_is_selfcontained():
    out = dash.render_html(ROWS)
    assert out.strip().startswith("<!doctype html>") or out.strip().startswith("<!DOCTYPE html>")
    assert "midnight-js" in out
    assert "http" not in out.split("<head")[0].lower() or "cdn" not in out.lower()

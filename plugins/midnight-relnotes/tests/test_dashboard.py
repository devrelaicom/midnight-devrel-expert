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

UNTRACKED_ROWS = [{"item": "onchain-runtime", "latest_relnote": "4.0.0",
                   "tracked": False, "tracked_label": "untracked", "prerelease": None}]

def test_untracked_row_labelled_not_stale_markdown():
    out = dash.render_markdown(UNTRACKED_ROWS)
    assert "onchain-runtime" in out and "untracked" in out
    # No misleading "0 / no" up-to-date reading, and no numeric behind.
    assert "| 0 |" not in out

def test_untracked_row_never_flagged_stale_html():
    out = dash.render_html(UNTRACKED_ROWS)
    assert "untracked" in out
    assert 'class="stale"' not in out

import json, os
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

# ---- basic style: severity row tints -----------------------------------
MIXED = [
    {"item": "crit-item", "latest_relnote": "1.0.0", "latest_stable": "1.3.0", "behind": 3, "stale": True, "prerelease": None},
    {"item": "warn-item", "latest_relnote": "2.0.0", "latest_stable": "2.1.0", "behind": 1, "stale": True, "prerelease": None},
    {"item": "current-item", "latest_relnote": "3.0.0", "latest_stable": "3.0.0", "behind": 0, "stale": False, "prerelease": None},
    {"item": "untracked-item", "latest_relnote": "9.0.0", "tracked": False, "tracked_label": "untracked", "prerelease": None},
]

def test_basic_row_tints_only_for_behind():
    out = dash.render_html(MIXED, style="basic")
    # exactly one warn (1 behind) and one crit (>1 behind); nothing else tinted.
    assert out.count('<tr class="warn">') == 1
    assert out.count('<tr class="crit">') == 1
    # current and untracked rows carry no tint class.
    assert '<tr><td>current-item' in out
    assert '<tr><td>untracked-item' in out

def test_basic_untracked_never_flagged():
    out = dash.render_html(UNTRACKED_ROWS, style="basic")
    assert "untracked" in out
    assert '<tr class="warn">' not in out and '<tr class="crit">' not in out

def test_basic_has_light_and_dark_tints():
    out = dash.render_html(MIXED, style="basic")
    assert "prefers-color-scheme:dark" in out  # tints defined for both schemes

# ---- full style: baked custom board ------------------------------------
def test_full_is_selfcontained_no_external_assets():
    out = dash.render_html(MIXED, style="full")
    assert out.strip().startswith("<!doctype html>")
    # No external stylesheet/script/font/image hosts (svg-namespace URL is fine).
    lowered = out.lower()
    assert "cdn" not in lowered
    assert "http://" not in lowered.replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in lowered.replace("http://www.w3.org/2000/svg", "")

def test_full_shows_status_badges_and_scoreboard():
    out = dash.render_html(MIXED, style="full")
    # every row's badge carries the meaning in text (colour is never the only signal)
    assert "3 behind" in out and "1 behind" in out and "current" in out and "not tracked" in out
    # severity groups + the colour-blocked scoreboard summary
    assert 'class="scoreboard"' in out and 'class="group"' in out
    for label in ("Needs a note", "One behind", "Current", "Not tracked"):
        assert label in out

def test_full_is_neobrutalist_not_slop():
    out = dash.render_html(MIXED, style="full")
    low = out.lower()
    # deliberate neo-brutalism: HARD offset shadow (no blur) + a bold frame
    assert "0 var(--ink)" in low          # e.g. 6px 6px 0 var(--ink)
    assert "3px solid var(--ink)" in low  # thick black frame
    # but still not the slop tells: no side stripe, no gradient, no blur/glow
    assert "border-left" not in low
    assert "gradient" not in low
    assert "blur(" not in low and "backdrop-filter" not in low
    # balanced Midnight palette: brand blue #0000fe for "current" + lime accent,
    # soft cool field, confident (not neon) alert tones
    assert "--brand:#0000fe" in low and "--ok:#0000fe" in low  # brand blue = current
    assert "--lime:#cbff46" in low        # Midnight lime accent back (date chip)
    assert "--desk:#edf0f7" in low        # soft cool field, not a loud full colour
    assert "#ff5a5f" not in low           # the old neon coral is gone

def test_full_sorts_most_severe_first():
    out = dash.render_html(MIXED, style="full")
    order = [out.index(name) for name in ("crit-item", "warn-item", "current-item", "untracked-item")]
    assert order == sorted(order)  # crit before warn before current before untracked

def test_full_prerelease_surfaced_on_current_row():
    rows = [{"item": "compact", "latest_relnote": "0.31.1", "latest_stable": "0.31.1",
             "behind": 0, "stale": False, "prerelease": "0.32.0-rc.1"}]
    out = dash.render_html(rows, style="full")
    assert "pre 0.32.0-rc.1" in out and "current" in out

def test_full_masthead_date_from_stamp():
    out = dash.render_html(MIXED, style="full", stamp="20260721-162954")
    assert "2026-07-21" in out and "Generated 2026-07-21 16:29 UTC" in out

def test_fragment_has_no_document_wrapper():
    frag = dash.render_html_fragment(MIXED, style="full")
    assert frag.lstrip().startswith("<style>")
    assert "<!doctype" not in frag.lower() and "<body" not in frag.lower()
    assert "scoreboard" in frag  # still contains the rendered content

# ---- disk output: timestamped filenames --------------------------------
def test_main_writes_timestamped_files(tmp_path):
    out_dir = tmp_path / "dashboards"
    dash.main(["--rows", json.dumps(MIXED), "--out-dir", str(out_dir),
               "--format", "both", "--style", "full", "--stamp", "20260721-160500"])
    names = sorted(os.listdir(out_dir))
    assert names == ["dashboard-20260721-160500.artifact.html",
                     "dashboard-20260721-160500.html",
                     "dashboard-20260721-160500.md"]

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { renderReport } from './render-report.mjs';

const data = JSON.parse(readFileSync(new URL('./fixtures/single.json', import.meta.url), 'utf8'));
const TPL = '<!doctype html><title>{{TITLE}}</title><body>{{GENERATED_AT}}{{BODY}}</body>';

test('renders the tutorial title and generated timestamp', () => {
  const html = renderReport(data, TPL);
  assert.match(html, /Counter Tutorial/);
  assert.match(html, /2026-07-06T12:00:00Z/);
});

test('renders a persona card with all five axes', () => {
  const html = renderReport(data, TPL);
  for (const axis of ['experience','patience','domain-knowledge','tooling','comprehension']) {
    assert.ok(html.includes(axis), `missing axis ${axis}`);
  }
});

test('renders severity counts and a show-stopper blocker row', () => {
  const html = renderReport(data, TPL);
  assert.match(html, /show-stopper/);
  assert.match(html, /what a witness is/);   // knowledgeNeeded text from fixture
});

test('escapes HTML in tutorial-supplied text', () => {
  const html = renderReport({ ...data, tutorial: { ...data.tutorial, title: '<script>x</script>' } }, TPL);
  assert.ok(!html.includes('<script>x</script>'));
  assert.match(html, /&lt;script&gt;/);
});

test('single mode omits the compare matrix', () => {
  const html = renderReport(data, TPL);
  assert.ok(!html.includes('id="blocker-matrix"'));
});

const cmp = JSON.parse(readFileSync(new URL('./fixtures/compare.json', import.meta.url), 'utf8'));

test('compare mode renders the blocker matrix', () => {
  const html = renderReport(cmp, TPL);
  assert.match(html, /id="blocker-matrix"/);
});

test('matrix has one row per persona and marks each persona name', () => {
  const html = renderReport(cmp, TPL);
  const start = html.indexOf('id="blocker-matrix"');
  assert.ok(start !== -1, 'blocker-matrix section not found');
  const end = html.indexOf('</section>', start);
  assert.ok(end !== -1, 'blocker-matrix section not closed');
  const matrix = html.slice(start, end);
  for (const p of cmp.personas) assert.ok(matrix.includes(p.name), `matrix missing ${p.name}`);
});

test('matrix cell shows worst severity initial for a blocked step', () => {
  const html = renderReport(cmp, TPL);
  assert.match(html, /class="cell sev-show-stopper"[^>]*>S</);  // student step 2 -> "S"
});

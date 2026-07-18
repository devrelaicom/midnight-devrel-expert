import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('plugin.json is valid JSON with required fields', () => {
  const raw = readFileSync('.claude-plugin/plugin.json', 'utf8');
  const m = JSON.parse(raw);
  assert.equal(m.name, 'midnight-tutorial-checker');
  assert.equal(typeof m.version, 'string');
  assert.equal(typeof m.description, 'string');
  assert.ok(m.description.length > 10, 'description should be meaningful');
});

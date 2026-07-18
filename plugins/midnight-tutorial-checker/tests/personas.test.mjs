import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const PRESETS = ['student', 'hobbyist', 'dev-new-to-web3', 'expert', 'non-native-speaker'];
const LEVELS = {
  experience: ['none','beginner','intermediate','expert'],
  patience: ['low','medium','high'],
  'domain-knowledge': ['none','some','strong'],
  tooling: ['none','some','strong'],
  comprehension: ['basic','intermediate','fluent','native'],
};

function parseFrontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  assert.ok(m, 'file must start with a --- frontmatter block');
  const obj = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([\w-]+):\s*(.+)$/);
    if (kv) obj[kv[1]] = kv[2].trim();
  }
  return obj;
}

for (const preset of PRESETS) {
  test(`${preset} defines all five axes with valid levels`, () => {
    const fm = parseFrontmatter(readFileSync(`skills/check-tutorial/personas/${preset}.md`, 'utf8'));
    assert.equal(fm.name, preset);
    for (const [axis, allowed] of Object.entries(LEVELS)) {
      assert.ok(allowed.includes(fm[axis]), `${preset}.${axis}="${fm[axis]}" not in ${allowed.join('|')}`);
    }
  });
}

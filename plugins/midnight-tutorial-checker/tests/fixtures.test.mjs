import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const LEVELS = {
  experience: ['none','beginner','intermediate','expert'],
  patience: ['low','medium','high'],
  'domain-knowledge': ['none','some','strong'],
  tooling: ['none','some','strong'],
  comprehension: ['basic','intermediate','fluent','native'],
};

const TYPES = ['smooth', 'assumed-knowledge', 'blocker', 'error'];
const SEVERITIES = ['info', 'minor', 'major', 'show-stopper'];

const FIXTURES = [
  'skills/check-tutorial/scripts/fixtures/single.json',
  'skills/check-tutorial/scripts/fixtures/compare.json',
];

for (const path of FIXTURES) {
  const data = JSON.parse(readFileSync(path, 'utf8'));

  for (const persona of data.personas) {
    test(`${path} :: ${persona.name} has exactly the five axes with valid levels`, () => {
      const axisKeys = Object.keys(persona.axes).sort();
      assert.deepEqual(axisKeys, Object.keys(LEVELS).sort());
      for (const [axis, allowed] of Object.entries(LEVELS)) {
        assert.ok(
          allowed.includes(persona.axes[axis]),
          `${persona.name}.${axis}="${persona.axes[axis]}" not in ${allowed.join('|')}`
        );
      }
    });

    test(`${path} :: ${persona.name} findings use valid type/severity enums`, () => {
      for (const f of persona.findings) {
        assert.ok(TYPES.includes(f.type), `${persona.name} step ${f.step}: invalid type "${f.type}"`);
        assert.ok(SEVERITIES.includes(f.severity), `${persona.name} step ${f.step}: invalid severity "${f.severity}"`);
      }
    });

    test(`${path} :: ${persona.name} smooth findings are always severity info`, () => {
      for (const f of persona.findings) {
        if (f.type === 'smooth') {
          assert.equal(f.severity, 'info', `${persona.name} step ${f.step}: smooth finding has severity "${f.severity}", expected "info"`);
        }
      }
    });

    test(`${path} :: ${persona.name} severityCounts sums to findings.length`, () => {
      const sum = Object.values(persona.severityCounts).reduce((a, b) => a + b, 0);
      assert.equal(sum, persona.findings.length);
    });
  }
}

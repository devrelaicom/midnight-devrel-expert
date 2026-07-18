#!/usr/bin/env node
// Deterministic, zero-dependency HTML report renderer.
// CLI: node render-report.mjs <report-data.json> <output.html>
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const AXES = ['experience', 'patience', 'domain-knowledge', 'tooling', 'comprehension'];
const SEVERITIES = ['info', 'minor', 'major', 'show-stopper'];

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function personaCard(p) {
  const rows = AXES.map((a) => `<div class="axis"><span class="axis-name">${esc(a)}</span><span class="axis-val val-${esc(p.axes[a])}">${esc(p.axes[a])}</span></div>`).join('');
  return `<section class="persona-card"><h3>${esc(p.name)}</h3>${rows}</section>`;
}

function verdict(p) {
  const status = p.verdict.completed ? 'completed' : 'blocked';
  const where = p.verdict.fellOffAtStep == null ? '' : ` at step ${esc(p.verdict.fellOffAtStep)}`;
  const counts = SEVERITIES.map((s) => `<span class="count sev-${esc(s)}">${esc(p.severityCounts[s] ?? 0)} ${esc(s)}</span>`).join('');
  return `<section class="verdict verdict-${status}"><h3>Verdict: ${status}${where}</h3><p>${esc(p.verdict.summary)}</p><div class="counts">${counts}</div></section>`;
}

function findingRow(f) {
  return `<tr class="sev-${esc(f.severity)} type-${esc(f.type)}">
    <td>${esc(f.step)}</td><td>${esc(f.title)}</td><td>${esc(f.type)}</td>
    <td>${esc(f.axis)}</td><td>${esc(f.severity)}</td>
    <td>${esc(f.groundTruthResult)}</td><td>${esc(f.knowledgeNeeded)}</td>
    <td>${esc(f.suggestedFix)}</td></tr>`;
}

function timeline(p) {
  const rows = p.findings.map(findingRow).join('');
  return `<section class="timeline"><h3>Step timeline — ${esc(p.name)}</h3>
    <table><thead><tr><th>#</th><th>Step</th><th>Type</th><th>Axis</th><th>Severity</th><th>Ran</th><th>Knowledge needed</th><th>Suggested fix</th></tr></thead>
    <tbody>${rows}</tbody></table></section>`;
}

function worstSeverityAt(findings, stepIndex) {
  let worst = -1;
  for (const f of findings) if (f.step === stepIndex) worst = Math.max(worst, SEVERITIES.indexOf(f.severity));
  return worst < 0 ? null : SEVERITIES[worst];
}

function matrix(data) {
  const head = data.steps.map((s) => `<th title="${esc(s.title)}">${esc(s.index)}</th>`).join('');
  const rows = data.personas.map((p) => {
    const cells = data.steps.map((s) => {
      const sev = worstSeverityAt(p.findings, s.index);
      const title = sev ? `${esc(s.title)} — ${esc(sev)}` : esc(s.title);
      return `<td class="cell ${sev ? 'sev-' + esc(sev) : 'sev-none'}" title="${title}">${sev ? esc(sev[0].toUpperCase()) : ''}</td>`;
    }).join('');
    return `<tr><th>${esc(p.name)}</th>${cells}</tr>`;
  }).join('');
  return `<section id="blocker-matrix" class="matrix"><h3>Blocker matrix</h3>
    <table><thead><tr><th>persona \\ step</th>${head}</tr></thead><tbody>${rows}</tbody></table></section>`;
}

export function renderReport(data, templateStr) {
  const parts = [`<section class="overview"><h2>${esc(data.tutorial.title)}</h2>
    <p class="source">Source: ${esc(data.tutorial.source)}</p></section>`];
  if (data.mode === 'compare' && data.personas.length > 1) parts.push(matrix(data));
  for (const p of data.personas) {
    parts.push(`<article class="persona-report">${personaCard(p)}${verdict(p)}${timeline(p)}</article>`);
  }
  return templateStr
    .replaceAll('{{TITLE}}', () => esc(data.tutorial.title))
    .replaceAll('{{GENERATED_AT}}', () => esc(data.generatedAt))
    .replaceAll('{{BODY}}', () => parts.join('\n'));
}

function main() {
  const [dataPath, outPath] = process.argv.slice(2);
  if (!dataPath || !outPath) { console.error('usage: render-report.mjs <data.json> <out.html>'); process.exit(2); }
  const data = JSON.parse(readFileSync(dataPath, 'utf8'));
  const tpl = readFileSync(new URL('../templates/report.html', import.meta.url), 'utf8');
  writeFileSync(outPath, renderReport(data, tpl));
  console.log(`wrote ${outPath}`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();

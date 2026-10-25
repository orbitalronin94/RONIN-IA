import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('Capacitor enables native HTTP for Android requests', () => {
  const config = JSON.parse(readFileSync(new URL('../capacitor.config.json', import.meta.url), 'utf8'));
  assert.equal(config.plugins?.CapacitorHttp?.enabled, true);
});

#!/usr/bin/env node
'use strict';

const { spawn } = require('child_process');
const path = require('path');

const repoRoot = __dirname;

// Prefer uv, fall back to python3.
const candidates = [
  ['uv', ['run', '--directory', repoRoot, 'src/server.py']],
  ['python3', [path.join(repoRoot, 'src', 'server.py')]],
];

let child = null;

function trySpawn(index) {
  if (index >= candidates.length) {
    console.error('japan-geospatial-open-data-mcp: no working Python runner (tried uv, python3)');
    process.exit(1);
  }
  const [cmd, args] = candidates[index];
  child = spawn(cmd, args, { stdio: ['inherit', 'inherit', 'inherit'], env: { ...process.env } });
  child.on('error', (err) => {
    console.error(`japan-geospatial-open-data-mcp: ${cmd} failed to start: ${err.message}`);
    trySpawn(index + 1);
  });
  child.on('exit', (code) => {
    process.exit(code == null ? 1 : code);
  });
}

trySpawn(0);

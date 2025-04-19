import { compat } from 'eslint-flat-config-utils';
import js from '@eslint/js';
import next from '@next/eslint-plugin-next';
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...compat(tseslint.configs.recommended),
  ...compat(next.configs.recommended),
  {
    ignores: [
      'node_modules/',
      'dist/',
      '.next/',
      'build/',
      'out/',
      'backend/',
      'venv/',
      'ENV/',
      '.venv/',
      '.git/',
      '.DS_Store',
      '*.py',
      '*.json',
      '*.md',
      '*.lock',
      '*.log',
    ],
  },
]; 
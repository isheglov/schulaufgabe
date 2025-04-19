import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';

const compat = new FlatCompat();

export default [
  js.configs.recommended,
  ...compat.config({
    extends: [
      'plugin:@next/next/recommended',
      'plugin:@typescript-eslint/recommended',
    ],
    plugins: ['@typescript-eslint'],
    parser: '@typescript-eslint/parser',
  }),
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
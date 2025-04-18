import js from '@eslint/js';
import next from '@next/eslint-plugin-next';
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  next.configs.recommended,
  {
    ignores: ['node_modules/', 'dist/', '.next/', 'build/', 'out/'],
  },
]; 
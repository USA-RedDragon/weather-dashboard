/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution');

module.exports = {
  root: true,
  extends: [
    'plugin:vue/vue3-essential',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier/skip-formatting',
    'google',
  ],
  rules: {
    'object-curly-spacing': ['error', 'always'],
    'require-jsdoc': 'off',
    // eslint-disable-next-line quote-props
    indent: ['error', 2, { SwitchCase: 1 }],
    'max-len': ['error', 120],
    'no-unused-vars': ['error', { varsIgnorePattern: '^_', argsIgnorePattern: '^_' }],
    'valid-jsdoc': 'off',
  },
  overrides: [
    {
      files: ['e2e/**/*.{test,spec}.{js,ts,jsx,tsx}'],
      extends: ['plugin:cypress/recommended'],
    },
  ],
  parserOptions: {
    ecmaVersion: 'latest',
  },
};

import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Minimal slate-based palette
        background: '#FFFFFF',
        surface: '#F8FAFC',
        border: '#E2E8F0',
        'text-primary': '#0F172A',
        'text-secondary': '#475569',
        'text-muted': '#94A3B8',
        accent: {
          DEFAULT: '#3B82F6',
          hover: '#60A5FA',
        },
        success: '#22C55E',
        error: '#EF4444',
      },
      fontFamily: {
        sans: ['-apple-system', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'JetBrains Mono', 'Menlo', 'monospace'],
      },
      animation: {
        'pulse-subtle': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

export default config
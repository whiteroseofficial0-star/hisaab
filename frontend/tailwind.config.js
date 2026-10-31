/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F5F1E8',
        surface: '#FFFCF6',
        ink: {
          DEFAULT: '#1C2823',
          soft: '#4B574F',
          muted: '#7A7D72',
        },
        pine: {
          50: '#EEF4F0',
          100: '#DCE9E2',
          200: '#BCD4C8',
          300: '#93B8A7',
          400: '#669982',
          500: '#447D68',
          600: '#2E6353',
          700: '#234F43',
          800: '#1C3F36',
          900: '#16332C',
          950: '#0C1E19',
        },
        line: '#DDD6C7',
        // Warm neutral scale, used across the existing markup.
        slate: {
          50: '#F7F3EA',
          100: '#F0EBDF',
          200: '#E2DACB',
          300: '#D0C7B6',
          400: '#AFA694',
          500: '#8B8372',
          600: '#6A6559',
          700: '#4E4B43',
          800: '#33332E',
          900: '#1E2723',
        },
        // Repoint indigo to the pine accent so legacy utility classes stay coherent.
        indigo: {
          50: '#EEF4F0',
          100: '#DCE9E2',
          200: '#BCD4C8',
          300: '#93B8A7',
          400: '#669982',
          500: '#447D68',
          600: '#2E6353',
          700: '#234F43',
          800: '#1C3F36',
          900: '#16332C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
        display: ['"Instrument Serif"', 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '3px',
        md: '5px',
        lg: '7px',
        xl: '10px',
      },
    },
  },
  plugins: [],
}

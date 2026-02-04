/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Primary Trust Blue (from PRD)
                primary: {
                    light: '#3B82F6', // Blue 500
                    DEFAULT: '#1E40AF', // Trust Blue - primary CTA, headers
                    dark: '#1E3A8A', // Blue 900
                },
                // Secondary colors
                secondary: {
                    light: '#94A3B8', // Slate 400
                    DEFAULT: '#64748B', // Slate 500
                    dark: '#475569', // Slate 600
                },
                // Corporate dark theme
                corporate: {
                    DEFAULT: '#1E293B', // Slate 800 - main sidebar bg
                    accent: '#334155', // Slate 700
                },
                // Status colors (from PRD)
                success: '#16A34A', // Green - compliant, approved
                warning: '#F59E0B', // Amber - review needed
                danger: '#DC2626', // Red - non-compliant, critical
                // Chat colors
                chat: {
                    user: '#FFFFFF',
                    bot: '#DBEAFE', // Blue 100
                    bg: '#F1F5F9', // Slate 100
                }
            },
            fontFamily: {
                sans: ['Inter', 'Poppins', 'ui-sans-serif', 'system-ui', 'sans-serif'],
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}

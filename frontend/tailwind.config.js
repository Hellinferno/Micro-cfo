/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    light: '#34D399', // Emerald 400
                    DEFAULT: '#10B981', // Emerald 500
                    dark: '#047857', // Darker for better contrast
                },
                secondary: {
                    light: '#94A3B8', // Slate 400
                    DEFAULT: '#64748B', // Slate 500
                    dark: '#475569', // Slate 600
                },
                corporate: {
                    DEFAULT: '#1E293B', // Slate 900 - Use for main headers/sidebar bg
                    accent: '#334155',
                },
                chat: {
                    user: '#FFFFFF',
                    bot: '#DCFCE7', // Emerald 100
                    bg: '#E2E8F0', // Slate 200 (WhatsApp background)
                }
            },
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}

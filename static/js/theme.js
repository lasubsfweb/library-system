/* static/js/theme.js */

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    const iconEl = toggleBtn ? toggleBtn.querySelector('i') : null;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    function applyTheme(isDark) {
        if (isDark) {
            htmlEl.setAttribute('data-theme', 'dark');
            if (iconEl) {
                iconEl.classList.remove('fa-moon');
                iconEl.classList.add('fa-sun');
            }
        } else {
            htmlEl.removeAttribute('data-theme');
            if (iconEl) {
                iconEl.classList.remove('fa-sun');
                iconEl.classList.add('fa-moon');
            }
        }
    }

    // Initial check
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && mediaQuery.matches)) {
        applyTheme(true);
    } else {
        applyTheme(false);
    }

    // Listen for system theme changes in real-time
    const handleThemeChange = (e) => {
        localStorage.removeItem('theme');
        applyTheme(e.matches);
    };

    if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', handleThemeChange);
    } else if (mediaQuery.addListener) {
        // Fallback for older browsers like older Safari
        mediaQuery.addListener(handleThemeChange);
    }

    // Manual toggle button
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = htmlEl.getAttribute('data-theme');
            if (currentTheme === 'dark') {
                applyTheme(false);
                localStorage.setItem('theme', 'light');
            } else {
                applyTheme(true);
                localStorage.setItem('theme', 'dark');
            }
        });
    }
});

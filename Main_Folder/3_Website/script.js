document.addEventListener('DOMContentLoaded', () => {
    // Mobile Navigation Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            
            // Toggle icon
            const icon = menuToggle.querySelector('i');
            if (navLinks.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    // Handle fake EXE download button click for demo
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Downloading "Sign Bridge Desktop App" Installer... (This feature works alongside the web version)');
        });
    }

    // INITIALIZE SPA
    // Get hash or default to home
    let hash = window.location.hash.replace('#', '');
    if(!hash || (hash !== 'home' && hash !== 'login' && hash !== 'profile' && hash !== 'project')) {
        hash = 'home';
    }
    navigateTo(hash);
});


// ==========================================
// SPA ROUTING LOGIC
// ==========================================
window.navigateTo = function(viewId, email = null) {
    const isAlreadyActive = document.getElementById('view-' + viewId) && document.getElementById('view-' + viewId).classList.contains('active-view');

    if (!isAlreadyActive) {
        // Hide all views synchronously to prevent layout shrinking/shaking
        document.querySelectorAll('.spa-view').forEach(view => {
            view.classList.remove('active-view');
            view.style.display = 'none';
        });
        
        const targetView = document.getElementById('view-' + viewId);
        if(targetView) {
            targetView.style.display = 'block';
            // slight delay before adding animation class is sometimes needed if we were targeting the *same* element, but we are targeting different ones, so synchronous is fine. 
            // Wait, actually forcing a reflow guarantees animation restarts if needed:
            void targetView.offsetWidth; 
            targetView.classList.add('active-view');
            window.scrollTo(0, 0);
        }
    }

    // Handle Navbar Buttons Display
    const loginLink = document.getElementById('login-nav-btn');
    const logoutLink = document.getElementById('logout-nav-btn');
    const mainNav = document.getElementById('main-nav');
    
    if (mainNav) {
        if (viewId === 'home') {
            mainNav.style.display = 'flex';
        } else {
            mainNav.style.display = 'none';
        }
    }

    if(loginLink && logoutLink) {
        if(viewId === 'profile' || viewId === 'project') {
            loginLink.style.display = 'none';
            logoutLink.style.display = 'block';
        } else {
            loginLink.style.display = 'block';
            logoutLink.style.display = 'none';
        }
    }

    // If profile view and email provided, update DOM
    if (viewId === 'profile' && email) {
        // give dom time to render
        setTimeout(() => {
            const emailElem = document.getElementById('user-email-display');
            if (emailElem) emailElem.textContent = email;
            const nameElem = document.getElementById('user-name-display');
            if (nameElem) {
                const namePart = email.split('@')[0];
                nameElem.textContent = namePart.charAt(0).toUpperCase() + namePart.slice(1);
            }
            const initialElem = document.getElementById('user-initial-display');
            if (initialElem) initialElem.textContent = email.charAt(0).toUpperCase();
        }, 20);
    }
    
    // Update URL Hash for back-button support without reloading
    if(window.history.pushState) {
        window.history.pushState(null, null, '#' + viewId);
    } else {
        window.location.hash = '#' + viewId;
    }
};

window.addEventListener('hashchange', function() {
    let hash = window.location.hash.replace('#', '');
    if(hash === 'home' || hash === 'login' || hash === 'profile' || hash === 'project') {
        navigateTo(hash);
    }
});

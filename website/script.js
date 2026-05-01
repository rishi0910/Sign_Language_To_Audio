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
        window.currentUserEmail = email;
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
            
            loadTranslationHistory(email);
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

// ==========================================
// NEW: Feedback & Translation History Logic
// ==========================================

window.submitFeedback = async function(event) {
    event.preventDefault();
    const email = document.getElementById('feedback-email').value;
    const message = document.getElementById('feedback-message').value;
    
    try {
        const res = await fetch('http://localhost:5000/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email.trim(), message: message.trim() })
        });
        
        if (res.ok) {
            document.getElementById('feedback-success').style.display = 'block';
            document.getElementById('feedback-form').reset();
            setTimeout(() => {
                document.getElementById('feedback-success').style.display = 'none';
            }, 3000);
        }
    } catch (err) {
        console.error("Failed to submit feedback", err);
        alert("Failed to submit feedback. Ensure backend is running.");
    }
};

window.simulateTranslation = async function() {
    const email = window.currentUserEmail || 'demo.user@college.edu';
    const sampleSigns = ["Hello", "Thank You", "How are you?", "Good Morning", "I need help", "Yes", "No", "Please"];
    const randomSign = sampleSigns[Math.floor(Math.random() * sampleSigns.length)];
    
    const resultDiv = document.getElementById('simulation-result');
    resultDiv.textContent = "Translating...";
    resultDiv.style.color = "#5f6368";
    
    setTimeout(async () => {
        try {
            await fetch('http://localhost:5000/api/translations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, signText: randomSign })
            });
            resultDiv.textContent = "Detected: " + randomSign;
            resultDiv.style.color = "#0F9D58";
        } catch(err) {
            console.error(err);
            resultDiv.textContent = "Failed to save to backend";
            resultDiv.style.color = "red";
        }
    }, 1000);
};

window.loadTranslationHistory = async function(email) {
    const container = document.getElementById('translation-history-container');
    if (!container) return;
    
    container.innerHTML = '<p style="color: #5f6368; text-align: center;">Loading history...</p>';
    
    try {
        const res = await fetch('http://localhost:5000/api/translations/' + encodeURIComponent(email));
        if (res.ok) {
            const history = await res.json();
            if (history.length === 0) {
                container.innerHTML = '<p style="color: #5f6368; text-align: center; margin: 0;">No translations yet. Start translating to see your history!</p>';
                return;
            }
            
            let html = '<ul style="list-style: none; padding: 0; margin: 0;">';
            history.forEach(item => {
                const dateStr = new Date(item.date).toLocaleString();
                html += `
                    <li style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eaeaea;">
                        <span style="font-weight: 500; color: #202124;">${item.signText}</span>
                        <span style="color: #5f6368; font-size: 0.9rem;">${dateStr}</span>
                    </li>
                `;
            });
            html += '</ul>';
            container.innerHTML = html;
        }
    } catch(err) {
        console.error(err);
        container.innerHTML = '<p style="color: red; text-align: center;">Failed to load history</p>';
    }
};

/**
 * OptiExam Core Client Script
 * 100% Offline Compatible (Zero CDN Dependencies)
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Fullscreen Toggle Handler
  const fullscreenBtn = document.getElementById('btn-fullscreen-toggle');
  if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
          console.warn('Fullscreen request failed:', err);
        });
      } else {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        }
      }
    });

    document.addEventListener('fullscreenchange', () => {
      const isFullscreen = !!document.fullscreenElement;
      fullscreenBtn.setAttribute('title', isFullscreen ? 'Exit Fullscreen' : 'Toggle Fullscreen');
      fullscreenBtn.setAttribute('aria-label', isFullscreen ? 'Exit Fullscreen' : 'Toggle Fullscreen');
      const iconUse = fullscreenBtn.querySelector('use');
      if (iconUse) {
        const baseHref = iconUse.getAttribute('href').split('#')[0];
        iconUse.setAttribute('href', `${baseHref}#${isFullscreen ? 'minimize' : 'maximize'}`);
      }
    });
  }

  // 2. Notification Bell Dropdown
  const notificationBell = document.getElementById('notification-bell');
  const notificationMenu = document.getElementById('notification-menu');
  if (notificationBell && notificationMenu) {
    notificationBell.addEventListener('click', (e) => {
      e.stopPropagation();
      notificationMenu.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!notificationMenu.contains(e.target) && e.target !== notificationBell) {
        notificationMenu.classList.remove('show');
      }
    });
  }

  // 3. Theme Toggle Handler
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (themeBtn) {
    themeBtn.addEventListener('click', async () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      
      const themeIcon = themeBtn.querySelector('use');
      if (themeIcon) {
        const baseHref = themeIcon.getAttribute('href').split('#')[0];
        themeIcon.setAttribute('href', `${baseHref}#${newTheme === 'dark' ? 'sun' : 'moon'}`);
      }

      // Sync with server session
      try {
        const csrfToken = getCookie('csrftoken');
        await fetch('/auth/theme-toggle/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        });
      } catch (err) {
        console.warn('Theme preference sync error:', err);
      }
    });
  }
});

/**
 * Utility helper to get cookie value by name (e.g. CSRF token)
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

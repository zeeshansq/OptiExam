/**
 * OptiExam Core Client Script Engine
 * 100% Offline Compatible (Zero CDN Dependencies)
 * Vanilla ES6+ Modular Client Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  initFullscreenToggle();
  initNotificationDropdown();
  initThemeToggle();
  initToastMessages();
  initFileDropzones();
  initAutoSlugify();
  initColorPickers();
  initCopyButtons();
  initFilterToolbar();
  initMarkCalculator();
  initUnsavedChangesGuard();
  initKeyboardShortcuts();
});

/* ==============================================================================
   1. Fullscreen Toggle Controller
   ============================================================================== */
function initFullscreenToggle() {
  const fullscreenBtn = document.getElementById('btn-fullscreen-toggle');
  if (!fullscreenBtn) return;

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

/* ==============================================================================
   2. In-App Notification Dropdown Controller
   ============================================================================== */
function initNotificationDropdown() {
  const notificationBell = document.getElementById('notification-bell');
  const notificationMenu = document.getElementById('notification-menu');
  if (!notificationBell || !notificationMenu) return;

  notificationBell.addEventListener('click', (e) => {
    e.stopPropagation();
    const isShowing = notificationMenu.classList.toggle('show');
    notificationBell.setAttribute('aria-expanded', isShowing ? 'true' : 'false');
  });

  document.addEventListener('click', (e) => {
    if (!notificationMenu.contains(e.target) && !notificationBell.contains(e.target)) {
      notificationMenu.classList.remove('show');
      notificationBell.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && notificationMenu.classList.contains('show')) {
      notificationMenu.classList.remove('show');
      notificationBell.setAttribute('aria-expanded', 'false');
    }
  });
}

/* ==============================================================================
   3. Dark / Light Theme Toggle & Session Synchronizer
   ============================================================================== */
function initThemeToggle() {
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (!themeBtn) return;

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

/* ==============================================================================
   4. Auto-Dismissing Toast / Flash Messages Controller
   ============================================================================== */
function initToastMessages() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert) => {
    // Add close button if not already present
    if (!alert.querySelector('.alert-close-btn')) {
      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'alert-close-btn';
      closeBtn.setAttribute('aria-label', 'Close');
      closeBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      `;
      closeBtn.addEventListener('click', () => dismissAlert(alert));
      alert.appendChild(closeBtn);
    }

    // Add progress bar
    if (!alert.querySelector('.alert-progress')) {
      const progress = document.createElement('div');
      progress.className = 'alert-progress';
      alert.appendChild(progress);
    }

    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      dismissAlert(alert);
    }, 5000);

    // Pause dismissal on mouse hover
    alert.addEventListener('mouseenter', () => {
      clearTimeout(timer);
      const progress = alert.querySelector('.alert-progress');
      if (progress) progress.style.animationPlayState = 'paused';
    });
  });
}

function dismissAlert(alert) {
  alert.classList.add('fade-out');
  setTimeout(() => {
    if (alert.parentNode) {
      alert.parentNode.removeChild(alert);
    }
  }, 350);
}

/* ==============================================================================
   5. Interactive Drag-and-Drop File Dropzone Controller
   ============================================================================== */
function initFileDropzones() {
  const dropzones = document.querySelectorAll('.file-dropzone');
  dropzones.forEach((dropzone) => {
    const parent = dropzone.closest('.form-group') || dropzone.parentElement;
    const fileInput = parent.querySelector('input[type="file"]');
    if (!fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        fileInput.files = files;
        updateDropzoneLabel(dropzone, files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        updateDropzoneLabel(dropzone, fileInput.files[0]);
      }
    });
  });
}

function updateDropzoneLabel(dropzone, file) {
  const labelStrong = dropzone.querySelector('strong');
  const labelSub = dropzone.querySelector('p');
  const sizeFormatted = file.size > 1048576 
    ? `${(file.size / 1048576).toFixed(2)} MB`
    : `${(file.size / 1024).toFixed(1)} KB`;

  if (labelStrong) {
    labelStrong.textContent = `✓ Selected: ${file.name}`;
    labelStrong.style.color = 'var(--color-accent)';
  }
  if (labelSub) {
    labelSub.textContent = `File Size: ${sizeFormatted} • Click to change`;
  }
}

/* ==============================================================================
   6. Auto-Slug & Code Generator Controller
   ============================================================================== */
function initAutoSlugify() {
  // Tenant Name -> Slug
  const nameInput = document.getElementById('id_name');
  const slugInput = document.getElementById('id_slug');
  if (nameInput && slugInput) {
    let userModifiedSlug = !!slugInput.value;
    slugInput.addEventListener('input', () => {
      userModifiedSlug = true;
    });

    nameInput.addEventListener('input', () => {
      if (!userModifiedSlug) {
        slugInput.value = nameInput.value
          .toLowerCase()
          .trim()
          .replace(/[^\w\s-]/g, '')
          .replace(/[\s_-]+/g, '-')
          .replace(/^-+|-+$/g, '');
      }
    });
  }

  // Exam Title -> Exam Code (Uppercase Acronym / Abbreviation)
  const examTitleInput = document.getElementById('id_title');
  const examCodeInput = document.getElementById('id_code');
  if (examTitleInput && examCodeInput) {
    let userModifiedCode = !!examCodeInput.value;
    examCodeInput.addEventListener('input', () => {
      userModifiedCode = true;
    });

    examTitleInput.addEventListener('input', () => {
      if (!userModifiedCode && examTitleInput.value.length >= 3) {
        const words = examTitleInput.value.trim().split(/\s+/);
        if (words.length >= 2) {
          const acronym = words.map(w => w.charAt(0).toUpperCase()).join('');
          examCodeInput.value = `${acronym}-2026`;
        }
      }
    });
  }
}

/* ==============================================================================
   7. Color Preset Palette Swatch Picker
   ============================================================================== */
function initColorPickers() {
  const colorInput = document.getElementById('id_primary_color');
  const swatches = document.querySelectorAll('.color-swatch-btn');
  if (!colorInput || swatches.length === 0) return;

  swatches.forEach((swatch) => {
    swatch.addEventListener('click', () => {
      const color = swatch.getAttribute('data-color');
      if (color) {
        colorInput.value = color;
        swatches.forEach(s => s.classList.remove('active'));
        swatch.classList.add('active');

        // Trigger input event
        colorInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });
}

/* ==============================================================================
   8. Copy to Clipboard Utility with Tooltip Feedback
   ============================================================================== */
function initCopyButtons() {
  const copyButtons = document.querySelectorAll('[data-copy]');
  copyButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const textToCopy = btn.getAttribute('data-copy');
      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
        const originalTooltip = btn.getAttribute('data-tooltip') || btn.getAttribute('title');
        btn.setAttribute('data-tooltip', 'Copied!');
        btn.classList.add('copied');

        setTimeout(() => {
          if (originalTooltip) {
            btn.setAttribute('data-tooltip', originalTooltip);
          } else {
            btn.removeAttribute('data-tooltip');
          }
          btn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        console.warn('Clipboard write failed:', err);
      }
    });
  });
}

/* ==============================================================================
   9. Single-Line Filter Toolbar Keyboard Shortcut & Clear Helper
   ============================================================================== */
function initFilterToolbar() {
  const searchInput = document.querySelector('.filter-search-field input[type="text"], .filter-search-field input[type="search"]');
  if (!searchInput) return;

  // Press "/" to focus search filter (when not typing in another input)
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
}

/* ==============================================================================
   10. Dynamic Marks / Weightage Live Summation Calculator
   ============================================================================== */
function initMarkCalculator() {
  // Rubric Max Points Totalizer
  const rubricInputs = document.querySelectorAll('input[name$="-max_points"]');
  const questionPointsInput = document.getElementById('id_points');
  if (rubricInputs.length > 0 && questionPointsInput) {
    const updateTotal = () => {
      let sum = 0;
      rubricInputs.forEach(input => {
        const val = parseFloat(input.value);
        if (!isNaN(val)) sum += val;
      });
      // Update hint or helper if sum differs
      if (sum > 0) {
        questionPointsInput.setAttribute('title', `Sum of criteria: ${sum.toFixed(1)} pts`);
      }
    };

    rubricInputs.forEach(input => {
      input.addEventListener('input', updateTotal);
    });
  }
}

/* ==============================================================================
   11. Form Unsaved Changes Guard
   ============================================================================== */
function initUnsavedChangesGuard() {
  const forms = document.querySelectorAll('form[method="post"]:not([data-no-guard])');
  forms.forEach((form) => {
    let isDirty = false;
    let isSubmitting = false;

    form.addEventListener('input', () => {
      isDirty = true;
    });

    form.addEventListener('submit', () => {
      isSubmitting = true;
      isDirty = false;
    });

    window.addEventListener('beforeunload', (e) => {
      if (isDirty && !isSubmitting) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    });
  });
}

/* ==============================================================================
   12. Global Keyboard Shortcuts Hub
   ============================================================================== */
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Ctrl+Enter or Cmd+Enter: Submit active form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const activeElement = document.activeElement;
      if (activeElement && activeElement.form) {
        e.preventDefault();
        activeElement.form.requestSubmit ? activeElement.form.requestSubmit() : activeElement.form.submit();
      }
    }
  });
}

/* ==============================================================================
   13. Global Helper Functions
   ============================================================================== */
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

/**
 * OptiExam Anti-Cheating & Proctoring Shield
 * 100% Offline Compatible (Zero CDN Dependencies)
 * Respects exam policy switches.
 */

class AntiCheatShield {
  constructor(config = {}) {
    this.enforceFullscreen = !!config.enforceFullscreen;
    this.lockCopyPaste = !!config.lockCopyPaste;
    this.isSimulation = !!config.isSimulation;
    this.maxViolations = config.maxViolations || 3;
    this.violationCount = config.violationCount || 0;
    this.onViolationCallback = config.onViolation || null;
    this.graceCountdownInterval = null;

    this.init();
  }


  init() {
    if (this.lockCopyPaste) {
      this.bindDOMEventLocks();
    }
    if (this.enforceFullscreen) {
      this.bindFullscreenLock();
      this.bindVisibilityMonitoring();
    }
  }

  bindDOMEventLocks() {
    // 1. Prevent Right-Click Context Menu
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      this.showToastWarning('Right-click context menu is disabled under exam lockdown policy.');
      this.logLocalViolation('CONTEXT_MENU_BLOCKED', 'Candidate attempted to open context menu.');
    }, true);

    // 2. Intercept Clipboard Copy, Cut & Paste Events
    ['copy', 'cut', 'paste'].forEach(evt => {
      document.addEventListener(evt, (e) => {
        // Disallow outside standard input or when clipboard lockdown is enabled
        const isQuillEditor = e.target && e.target.closest('.ql-editor');
        if (!isQuillEditor) {
          e.preventDefault();
          this.showToastWarning(`Clipboard action (${evt.toUpperCase()}) is disabled by proctoring policy.`);
          this.logLocalViolation('CLIPBOARD_BLOCKED', `Blocked clipboard action: ${evt}`);
        }
      }, true);
    });

    // 3. Prevent Drag & Drop Text/Assets
    document.addEventListener('dragstart', (e) => {
      e.preventDefault();
    }, true);

    // 4. Intercept inspect & devtools shortcut keys
    document.addEventListener('keydown', (e) => {
      const isEditable = e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.closest('.ql-editor'));
      if (
        e.key === 'F12' ||
        (!isEditable && (e.ctrlKey || e.metaKey) && ['c', 'v', 'p', 'u', 's', 'a'].includes(e.key.toLowerCase())) ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i', 'j', 'c', 'k', 'm'].includes(e.key.toLowerCase()))
      ) {
        e.preventDefault();
        this.showToastWarning('Inspection & developer shortcut keys are restricted.');
        this.logLocalViolation('DEVTOOLS_BLOCKED', `Blocked key combination: ${e.key}`);
      }
    }, true);
  }

  showToastWarning(msg) {
    let toast = document.getElementById('cockpit-security-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'cockpit-security-toast';
      toast.className = 'security-toast-pill';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }




  bindVisibilityMonitoring() {
    let wasBlurred = false;

    window.addEventListener('blur', () => {
      if (!wasBlurred) {
        wasBlurred = true;
        this.handleViolation('TAB_BLUR', 'Window lost focus or candidate switched tabs.');
      }
    });

    window.addEventListener('focus', () => {
      wasBlurred = false;
    });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.handleViolation('TAB_BLUR', 'Candidate navigated away from examination tab.');
      }
    });
  }

  bindFullscreenLock() {
    const entryOverlay = document.getElementById('fullscreen-entry-overlay');
    const btnEnterInitialFs = document.getElementById('btn-enter-initial-fullscreen');

    // Prompt candidate immediately if fullscreen is not active on startup
    if (!document.fullscreenElement && entryOverlay) {
      entryOverlay.classList.add('show');
    }

    if (btnEnterInitialFs && entryOverlay) {
      btnEnterInitialFs.addEventListener('click', () => {
        document.documentElement.requestFullscreen().then(() => {
          entryOverlay.classList.remove('show');
        }).catch(err => {
          console.warn('Initial fullscreen request failed:', err);
          entryOverlay.classList.remove('show');
        });
      });
    }

    // Monitor ongoing fullscreen status changes
    document.addEventListener('fullscreenchange', () => {
      const isFullscreen = !!document.fullscreenElement;
      const overlay = document.getElementById('fullscreen-alert-overlay');

      if (!isFullscreen) {
        if (overlay) {
          overlay.classList.add('show');
          this.startFullscreenGraceTimer();
        }
        this.handleViolation('FULLSCREEN_EXIT', 'Candidate exited fullscreen lockdown mode.');
      } else {
        if (overlay) overlay.classList.remove('show');
        if (entryOverlay) entryOverlay.classList.remove('show');
        if (this.graceCountdownInterval) {
          clearInterval(this.graceCountdownInterval);
          this.graceCountdownInterval = null;
        }
      }
    });

    // If candidate clicks the Return to Fullscreen button
    const btnReturnFs = document.getElementById('btn-return-fullscreen');
    if (btnReturnFs) {
      btnReturnFs.addEventListener('click', () => {
        document.documentElement.requestFullscreen().catch(err => {
          console.warn('Fullscreen request failed:', err);
        });
      });
    }
  }




  startFullscreenGraceTimer() {
    let remainingGrace = 15;
    const graceTimerDisplay = document.getElementById('fullscreen-grace-seconds');
    if (graceTimerDisplay) graceTimerDisplay.textContent = remainingGrace;

    if (this.graceCountdownInterval) clearInterval(this.graceCountdownInterval);
    this.graceCountdownInterval = setInterval(() => {
      remainingGrace -= 1;
      if (graceTimerDisplay) graceTimerDisplay.textContent = remainingGrace;
      if (remainingGrace <= 0) {
        clearInterval(this.graceCountdownInterval);
        this.handleViolation('FULLSCREEN_GRACE_EXPIRED', 'Candidate failed to return to fullscreen within 15 seconds.');
      }
    }, 1000);
  }

  handleViolation(type, message) {
    this.violationCount += 1;
    const countBadge = document.getElementById('violation-counter-pill');
    if (countBadge) countBadge.textContent = `${this.violationCount} Violations`;

    if (this.onViolationCallback) {
      this.onViolationCallback(type, message, this.violationCount);
    }
  }

  logLocalViolation(type, message) {
    if (this.onViolationCallback) {
      this.onViolationCallback(type, message, this.violationCount);
    }
  }
}

window.AntiCheatShield = AntiCheatShield;

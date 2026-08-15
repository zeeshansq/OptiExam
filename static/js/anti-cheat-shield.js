/**
 * OptiExam Anti-Cheating & Proctoring Shield
 * 100% Offline Compatible (Zero CDN Dependencies)
 * Respects exam policy switches.
 */

class AntiCheatShield {
  constructor(config = {}) {
    this.enforceFullscreen = !!config.enforceFullscreen;
    this.lockCopyPaste = !!config.lockCopyPaste;
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
    // Intercept inspect & shortcut keys only outside input elements
    document.addEventListener('keydown', (e) => {
      const isEditable = e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA');
      if (
        e.key === 'F12' ||
        (!isEditable && (e.ctrlKey || e.metaKey) && ['c', 'v', 'p', 'u', 's'].includes(e.key.toLowerCase())) ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && ['i', 'j', 'c'].includes(e.key.toLowerCase()))
      ) {
        e.preventDefault();
        this.logLocalViolation('DEVTOOLS_BLOCKED', `Blocked key combination: ${e.key}`);
      }
    }, true);
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
    document.addEventListener('fullscreenchange', () => {
      const isFullscreen = !!document.fullscreenElement;
      const overlay = document.getElementById('fullscreen-alert-overlay');

      if (!isFullscreen) {
        if (overlay) overlay.classList.add('show');
        this.handleViolation('FULLSCREEN_EXIT', 'Candidate exited fullscreen lockdown mode.');
        this.startFullscreenGraceTimer();
      } else {
        if (overlay) overlay.classList.remove('show');
        if (this.graceCountdownInterval) {
          clearInterval(this.graceCountdownInterval);
          this.graceCountdownInterval = null;
        }
      }
    });
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

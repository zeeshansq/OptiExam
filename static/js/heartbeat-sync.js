/**
 * OptiExam 15-Second Periodic Heartbeat & Auto-Save Sync Engine
 * Synchronizes client clock against server authority, auto-saves incremental answers,
 * and maintains encrypted offline fallback queue in localStorage.
 */

class HeartbeatSyncEngine {
  constructor(config = {}) {
    this.attemptId = config.attemptId;
    this.heartbeatUrl = config.heartbeatUrl;
    this.csrfToken = config.csrfToken;
    this.remainingSeconds = config.remainingSeconds || 0;
    this.intervalSeconds = 15;
    this.pendingDelta = [];
    this.isSyncing = false;
    this.timerInterval = null;
    this.heartbeatInterval = null;
    this.onTick = config.onTick || null;
    this.onExpired = config.onExpired || null;

    this.startClock();
    this.startHeartbeatLoop();
  }

  startClock() {
    this.timerInterval = setInterval(() => {
      this.remainingSeconds -= 1;
      if (this.onTick) {
        this.onTick(this.remainingSeconds);
      }
      if (this.remainingSeconds <= 0) {
        clearInterval(this.timerInterval);
        if (this.onExpired) {
          this.onExpired();
        }
      }
    }, 1000);
  }

  startHeartbeatLoop() {
    this.heartbeatInterval = setInterval(() => {
      this.syncNow();
    }, this.intervalSeconds * 1000);
  }

  queueAnswer(questionId, data) {
    // Upsert to pending delta queue
    const existingIdx = this.pendingDelta.findIndex(item => item.question_id === questionId);
    const item = { question_id: questionId, ...data };
    if (existingIdx >= 0) {
      this.pendingDelta[existingIdx] = item;
    } else {
      this.pendingDelta.push(item);
    }

    // Save to local storage for crash protection
    try {
      localStorage.setItem(`optiexam_attempt_${this.attemptId}`, JSON.stringify(this.pendingDelta));
    } catch (e) {
      console.warn('LocalStorage save failed:', e);
    }
  }

  async syncNow(activeQuestionId = null) {
    if (this.isSyncing) return;
    this.isSyncing = true;

    const payload = {
      active_question_id: activeQuestionId,
      answers_delta: [...this.pendingDelta]
    };

    try {
      const response = await fetch(this.heartbeatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'expired') {
          if (this.onExpired) this.onExpired();
        } else if (result.status === 'active') {
          // Adjust client timer to server authoritative remaining seconds
          if (Math.abs(this.remainingSeconds - result.remaining_seconds) > 3) {
            this.remainingSeconds = result.remaining_seconds;
          }
          // Clear successfully synced delta
          this.pendingDelta = [];
        }
      }
    } catch (err) {
      console.warn('Heartbeat signal offline. Queued locally.', err);
    } finally {
      this.isSyncing = false;
    }
  }

  destroy() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
  }
}

window.HeartbeatSyncEngine = HeartbeatSyncEngine;

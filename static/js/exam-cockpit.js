/**
 * OptiExam Interactive Examination Cockpit Controller
 * Clean, Robust, Modular Execution
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!window.COCKPIT_CONFIG) return;

  const config = window.COCKPIT_CONFIG;
  let currentQuestionIndex = parseInt(config.activeQuestionIndex, 10) || 0;

  // Try recovering last viewed question index from localStorage if valid
  try {
    const savedIdx = localStorage.getItem(`optiexam_current_q_${config.attemptId}`);
    if (savedIdx !== null) {
      const parsed = parseInt(savedIdx, 10);
      if (!isNaN(parsed) && parsed >= 0 && parsed < (config.questions || []).length) {
        currentQuestionIndex = parsed;
      }
    }
  } catch (e) {
    console.warn('Could not read saved question index:', e);
  }

  const questions = config.questions || [];
  let currentFontSize = 1.15;


  // 1. Cache all DOM Elements upfront
  const btnPrev = document.getElementById('btn-prev-question');
  const btnNext = document.getElementById('btn-next-question');
  const btnBookmark = document.getElementById('btn-toggle-bookmark');
  const bookmarkBtnText = document.getElementById('bookmarkBtnText');
  const btnClear = document.getElementById('btn-clear-answer');
  const btnFontDec = document.getElementById('btn-font-dec');
  const btnFontInc = document.getElementById('btn-font-inc');
  const btnTheme = document.getElementById('btn-theme-toggle');
  const btnOpenInstructions = document.getElementById('btn-open-instructions');
  const btnCloseInstructions = document.getElementById('btn-close-instructions');
  const instructionsModal = document.getElementById('instructions-modal');
  const submitConfirmModal = document.getElementById('submit-confirm-modal');
  const btnTriggerSubmit = document.getElementById('btn-trigger-submit-modal');
  const btnCancelSubmit = document.getElementById('btn-cancel-submit-modal');
  const btnFiftyFifty = document.getElementById('btn-lifeline-fifty');
  const btnHint = document.getElementById('btn-lifeline-hint');
  const hintModal = document.getElementById('lifeline-hint-modal');
  const hintContent = document.getElementById('lifeline-hint-content');
  const btnCloseHint = document.getElementById('btn-close-hint-modal');
  const btnDismissHint = document.getElementById('btn-dismiss-hint');
  const btnReturnFullscreen = document.getElementById('btn-return-fullscreen');

  // Custom Modal Dialog Engine (Replaces browser alert/confirm)
  const dialogOverlay = document.getElementById('cockpit-custom-dialog-overlay');
  const dialogTitle = document.getElementById('cockpit-dialog-title');
  const dialogMsg = document.getElementById('cockpit-dialog-message');
  const btnDialogConfirm = document.getElementById('btn-dialog-confirm');
  const btnDialogCancel = document.getElementById('btn-dialog-cancel');

  function showCockpitDialog(title, message, isConfirm = false) {
    return new Promise((resolve) => {
      if (!dialogOverlay) {
        if (isConfirm) resolve(window.confirm(message));
        else { window.alert(message); resolve(true); }
        return;
      }

      dialogTitle.textContent = title;
      dialogMsg.textContent = message;

      btnDialogCancel.style.display = isConfirm ? 'inline-flex' : 'none';
      dialogOverlay.classList.add('show');

      function onConfirm() {
        cleanup();
        resolve(true);
      }

      function onCancel() {
        cleanup();
        resolve(false);
      }

      function cleanup() {
        dialogOverlay.classList.remove('show');
        btnDialogConfirm.removeEventListener('click', onConfirm);
        btnDialogCancel.removeEventListener('click', onCancel);
      }

      btnDialogConfirm.addEventListener('click', onConfirm);
      btnDialogCancel.addEventListener('click', onCancel);
    });
  }



  // 2. Initialize Heartbeat Sync Engine
  const heartbeat = new HeartbeatSyncEngine({
    attemptId: config.attemptId,
    heartbeatUrl: config.heartbeatUrl,
    csrfToken: config.csrfToken,
    remainingSeconds: config.remainingSeconds,
    onTick: (seconds) => updateTimerDisplay(seconds),
    onExpired: () => handleExamExpired()
  });

  // Intercept Sync Pulse for UI Indicator
  const originalSyncNow = heartbeat.syncNow.bind(heartbeat);
  heartbeat.syncNow = async function(activeQuestionId = null) {
    const syncPill = document.getElementById('syncStatusPill');
    const syncText = document.getElementById('syncStatusText');
    if (syncPill) syncPill.classList.add('syncing');
    if (syncText) syncText.textContent = 'Syncing...';
    
    try {
      await originalSyncNow(activeQuestionId);
      if (syncText) syncText.textContent = 'Synced';
    } catch (e) {
      if (syncText) syncText.textContent = 'Offline Saved';
    } finally {
      if (syncPill) syncPill.classList.remove('syncing');
    }
  };

  // 3. Initialize Anti-Cheat Shield (Passive if disabled)
  const violationHistory = [];
  const violationAuditModal = document.getElementById('violation-audit-modal');
  const btnCloseViolation = document.getElementById('btn-close-violation-modal');
  const btnDismissViolation = document.getElementById('btn-dismiss-violation-modal');
  const violationCounterPill = document.getElementById('violation-counter-pill');

  if (violationCounterPill && violationAuditModal) {
    violationCounterPill.style.cursor = 'pointer';
    violationCounterPill.addEventListener('click', () => {
      renderViolationAuditList();
      violationAuditModal.classList.add('show');
    });
  }

  if (btnCloseViolation && violationAuditModal) {
    btnCloseViolation.addEventListener('click', () => violationAuditModal.classList.remove('show'));
  }
  if (btnDismissViolation && violationAuditModal) {
    btnDismissViolation.addEventListener('click', () => violationAuditModal.classList.remove('show'));
  }

  function renderViolationAuditList() {
    const listElem = document.getElementById('violation-audit-list');
    if (!listElem) return;

    if (violationHistory.length === 0) {
      listElem.innerHTML = `
        <div class="glass-card" style="padding: 12px 16px; font-size: 0.84rem; color: var(--cockpit-text-muted); text-align: center;">
          No security violations recorded in this session.
        </div>
      `;
      return;
    }

    listElem.innerHTML = violationHistory.map(v => `
      <div class="glass-card flex items-center justify-between" style="padding: 10px 14px; border-left: 3px solid var(--cockpit-danger); border-radius: 6px; background: rgba(239, 68, 68, 0.06);">
        <div>
          <div style="font-weight: 700; font-size: 0.85rem; color: var(--cockpit-text-main);">${v.title}</div>
          <div style="font-size: 0.78rem; color: var(--cockpit-text-muted); margin-top: 2px;">${v.message}</div>
        </div>
        <div style="font-size: 0.74rem; font-family: var(--font-mono); color: #38BDF8; white-space: nowrap;">
          ${v.time}
        </div>
      </div>
    `).join('');
  }

  const antiCheat = new AntiCheatShield({
    enforceFullscreen: config.enforceFullscreen,
    lockCopyPaste: config.lockCopyPaste,
    isSimulation: config.isSimulation,
    maxViolations: config.maxTabSwitchLimit || config.maxViolations || 3,
    onViolation: async (type, message, count) => {
      const now = new Date();
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
      
      const typeTitles = {
        'TAB_BLUR': 'Window Lost Focus / Tab Switch',
        'FULLSCREEN_EXIT': 'Fullscreen Lockdown Exited',
        'FULLSCREEN_GRACE_EXPIRED': 'Fullscreen Return Grace Timeout',
        'CLIPBOARD_BLOCKED': 'Clipboard Action Blocked',
        'CONTEXT_MENU_BLOCKED': 'Context Menu Blocked',
        'DEVTOOLS_BLOCKED': 'DevTools / Key Lock Blocked'
      };

      violationHistory.unshift({
        type,
        title: typeTitles[type] || type,
        message: message || 'Proctoring rule violation recorded.',
        time: timeStr
      });

      const countBadge = document.getElementById('violation-counter-pill');
      const countText = document.getElementById('violation-count-text');
      if (countBadge && count > 0) {
        countBadge.style.display = 'inline-flex';
        if (countText) countText.textContent = `${count} Violation${count > 1 ? 's' : ''}`;
      }

      try {
        const resp = await fetch(config.violationUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': config.csrfToken
          },
          body: JSON.stringify({ event_type: type, details: { message } })
        });
        const data = await resp.json();

        if (data.is_auto_submitted) {
          // Trigger Security Limit Reached Modal (NOT Time Expired)
          const violationModal = document.getElementById('violation-escalation-modal');
          if (violationModal) {
            const msgElem = document.getElementById('violation-escalation-msg');
            if (msgElem) {
              msgElem.textContent = `You have reached the maximum allowed limit (${data.max_violations || count} violations). Your assessment has been automatically finalized.`;
            }
            violationModal.classList.add('show');
          }
          setTimeout(() => {
            window.location.href = config.submitUrl;
          }, 2500);
        } else if (data.max_violations && (data.max_violations - count) <= 2 && (data.max_violations - count) > 0) {
          // Warning popup when 2 switches/violations left before auto-submit
          const remainingSwitches = data.max_violations - count;
          await showCockpitDialog(
            'Security Warning: Tab Switch Detected',
            `You have switched away from the exam window. You only have ${remainingSwitches} switch${remainingSwitches > 1 ? 'es' : ''} remaining before your assessment is automatically submitted.`
          );
        }
      } catch (e) {
        console.warn('Violation logging failed:', e);
      }
    }
  });



  // 4. Restore any unsynced local answers on page reload for crash recovery
  try {
    const cachedPending = localStorage.getItem(`optiexam_attempt_${config.attemptId}`);
    if (cachedPending) {
      const pendingList = JSON.parse(cachedPending);
      if (Array.isArray(pendingList)) {
        pendingList.forEach(item => {
          const targetQ = questions.find(q => q.question_id === item.question_id);
          if (targetQ && targetQ.answer) {
            if (item.text_response !== undefined) {
              targetQ.answer.text_response = item.text_response;
              targetQ.answer.is_answered = !!item.text_response.trim();
            }
            if (item.selected_option_ids !== undefined) {
              targetQ.answer.selected_option_ids = item.selected_option_ids;
              targetQ.answer.is_answered = item.selected_option_ids.length > 0;
            }
            if (item.is_bookmarked !== undefined) {
              targetQ.answer.is_bookmarked = item.is_bookmarked;
            }
          }
        });
      }
    }
  } catch (e) {
    console.warn('Could not restore local storage answers:', e);
  }

  // Flush answers immediately on beforeunload / pagehide using Navigator sendBeacon or sync
  window.addEventListener('beforeunload', () => {
    const activeQ = questions[currentQuestionIndex];
    if (activeQ && heartbeat.pendingDelta.length > 0) {
      const payload = JSON.stringify({
        active_question_id: activeQ.question_id,
        answers_delta: heartbeat.pendingDelta
      });
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon(config.heartbeatUrl, blob);
      }
    }
  });

  // 5. Theme Toggle Button
  if (btnTheme) {
    btnTheme.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      
      const themeIcon = btnTheme.querySelector('use');
      if (themeIcon) {
        const baseHref = themeIcon.getAttribute('href').split('#')[0];
        themeIcon.setAttribute('href', `${baseHref}#${newTheme === 'dark' ? 'sun' : 'moon'}`);
      }
    });
  }

  // 6. Initialize Quill Rich Text Editor
  let quillInstance = null;
  let isUpdatingQuillProgrammatically = false;
  const quillContainer = document.getElementById('quill-editor-container');
  if (quillContainer && window.Quill) {
    quillInstance = new Quill('#quill-editor-container', {
      theme: 'snow',
      placeholder: 'Type your comprehensive response here... Use toolbar tools for formatting, equations, lists, and code.',
      modules: {
        toolbar: [
          [{ 'header': [1, 2, 3, false] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ 'color': [] }, { 'background': [] }],
          [{ 'script': 'sub'}, { 'script': 'super' }],
          [{ 'list': 'ordered'}, { 'list': 'bullet' }],
          ['blockquote', 'code-block'],
          ['clean']
        ]
      }
    });

    quillInstance.on('text-change', (delta, oldDelta, source) => {
      if (isUpdatingQuillProgrammatically) return;

      const q = questions[currentQuestionIndex];
      if (!q) return;

      const html = quillInstance.root.innerHTML;
      const text = quillInstance.getText().trim();
      const count = text ? text.split(/\s+/).filter(Boolean).length : 0;

      const wordCountSpan = document.getElementById('word-count-num');
      if (wordCountSpan) wordCountSpan.textContent = count;

      q.answer.text_response = text ? html : '';
      q.answer.is_answered = count > 0;

      updatePaletteTileStatus(currentQuestionIndex, q.answer);
      updateGlobalStatsHUD();

      heartbeat.queueAnswer(q.question_id, { text_response: q.answer.text_response });
    });
  }

  // 7. Initial Stats & Initial Question Render
  updateGlobalStatsHUD();
  renderQuestion(currentQuestionIndex);


  // 6. Navigation Buttons (Respect allow_back_navigation policy)
  if (btnPrev) {
    if (!config.allowBackNavigation) {
      btnPrev.style.display = 'none';
    } else {
      btnPrev.addEventListener('click', () => {
        if (currentQuestionIndex > 0) {
          currentQuestionIndex -= 1;
          renderQuestion(currentQuestionIndex);
        }
      });
    }
  }

  if (btnNext) {
    btnNext.addEventListener('click', async () => {
      const q = questions[currentQuestionIndex];
      // If linear navigation policy is enforced, candidate MUST answer the question before advancing
      if (!config.allowBackNavigation && (!q.answer || !q.answer.is_answered)) {
        await showCockpitDialog(
          'Answer Required',
          'Linear exam progression is enforced. You must answer or attempt this question before saving and moving to the next question.'
        );
        return;
      }

      if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex += 1;
        renderQuestion(currentQuestionIndex);
      } else {
        // At the last question, trigger final submission review
        if (btnTriggerSubmit) btnTriggerSubmit.click();
      }
    });
  }

  // 7. Bind Palette Tiles (Enforcing linear progression if back navigation is disabled)
  document.querySelectorAll('.palette-tile').forEach((tile) => {
    tile.addEventListener('click', async () => {
      const idx = parseInt(tile.getAttribute('data-index'), 10);
      if (!isNaN(idx) && idx >= 0 && idx < questions.length) {
        if (!config.allowBackNavigation) {
          if (idx !== currentQuestionIndex) {
            await showCockpitDialog(
              'Sequential Navigation Enforced',
              'Direct palette jumping is disabled for this examination. Please use "Save Answer & Next" to progress through questions sequentially.'
            );
            return;
          }
        }
        currentQuestionIndex = idx;
        renderQuestion(currentQuestionIndex);
      }
    });
  });



  // 8. Bookmark / Flag Toggle Button (Disabled if linear progression is enforced)
  if (btnBookmark) {
    if (!config.allowBackNavigation) {
      btnBookmark.style.display = 'none';
    } else {
      btnBookmark.addEventListener('click', () => {
        const q = questions[currentQuestionIndex];
        if (!q) return;

        q.answer.is_bookmarked = !q.answer.is_bookmarked;
        updateBookmarkButtonState(q.answer.is_bookmarked);
        updatePaletteTileStatus(currentQuestionIndex, q.answer);
        updateGlobalStatsHUD();

        heartbeat.queueAnswer(q.question_id, { is_bookmarked: q.answer.is_bookmarked });
      });
    }
  }

  // 9. Clear Answer Button
  if (btnClear) {
    btnClear.addEventListener('click', async () => {
      const q = questions[currentQuestionIndex];
      if (!q) return;

      const confirmed = await showCockpitDialog('Clear Response', 'Are you sure you want to clear your current answer for this question?', true);
      if (!confirmed) return;

      if (['MCQ_SINGLE', 'MCQ_MULTIPLE', 'IMAGE_MCQ'].includes(q.question_type)) {
        q.answer.selected_option_ids = [];
        const container = document.getElementById('mcq-options-area');
        if (container) {
          container.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
        }
      } else {
        q.answer.text_response = '';
        if (quillInstance) {
          quillInstance.setText('');
        }
        const wordCountSpan = document.getElementById('word-count-num');
        if (wordCountSpan) wordCountSpan.textContent = '0';
      }

      q.answer.is_answered = false;
      updatePaletteTileStatus(currentQuestionIndex, q.answer);
      updateGlobalStatsHUD();

      heartbeat.queueAnswer(q.question_id, {
        selected_option_ids: q.answer.selected_option_ids || [],
        text_response: q.answer.text_response || ''
      });
    });
  }




  // 11. Font Size Scaler
  const readingArea = document.getElementById('current-question-prompt');
  if (btnFontDec && readingArea) {
    btnFontDec.addEventListener('click', () => {
      if (currentFontSize > 0.95) {
        currentFontSize -= 0.1;
        readingArea.style.fontSize = `${currentFontSize}rem`;
      }
    });
  }

  if (btnFontInc && readingArea) {
    btnFontInc.addEventListener('click', () => {
      if (currentFontSize < 1.6) {
        currentFontSize += 0.1;
        readingArea.style.fontSize = `${currentFontSize}rem`;
      }
    });
  }

  // 12. Instructions Modal
  if (btnOpenInstructions && instructionsModal) {
    btnOpenInstructions.addEventListener('click', () => {
      instructionsModal.classList.add('show');
    });
  }

  if (btnCloseInstructions && instructionsModal) {
    btnCloseInstructions.addEventListener('click', () => {
      instructionsModal.classList.remove('show');
    });
  }

  // 13. Pre-Submit Modal Controls
  if (btnTriggerSubmit && submitConfirmModal) {
    btnTriggerSubmit.addEventListener('click', () => {
      let answeredCount = 0;
      let bookmarkedCount = 0;

      questions.forEach(q => {
        if (q.answer && q.answer.is_answered) answeredCount += 1;
        if (q.answer && q.answer.is_bookmarked) bookmarkedCount += 1;
      });

      const unansweredCount = questions.length - answeredCount;

      const statAns = document.getElementById('modal-stat-answered');
      const statBkm = document.getElementById('modal-stat-bookmarked');
      const statUna = document.getElementById('modal-stat-unanswered');

      if (statAns) statAns.textContent = answeredCount;
      if (statBkm) statBkm.textContent = bookmarkedCount;
      if (statUna) statUna.textContent = unansweredCount;

      submitConfirmModal.classList.add('show');
    });
  }

  if (btnCancelSubmit && submitConfirmModal) {
    btnCancelSubmit.addEventListener('click', () => {
      submitConfirmModal.classList.remove('show');
    });
  }

  // 14. Keyboard Shortcuts (Alt+Right: Next, Alt+Left: Prev, Alt+F: Flag)
  document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key === 'ArrowRight') {
      e.preventDefault();
      if (btnNext) btnNext.click();
    } else if (e.altKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      if (config.allowBackNavigation && btnPrev) {
        btnPrev.click();
      }
    } else if (e.altKey && (e.key === 'f' || e.key === 'F')) {
      e.preventDefault();
      if (config.allowBackNavigation && btnBookmark) {
        btnBookmark.click();
      }
    }
  });


  function renderQuestion(index) {
    const q = questions[index];
    if (!q) return;

    // Update Meta info
    const numElem = document.getElementById('current-question-num');
    const ptsElem = document.getElementById('current-question-points');
    const typeElem = document.getElementById('current-question-type-badge');
    const promptElem = document.getElementById('current-question-prompt');

    if (numElem) numElem.textContent = `Question ${q.order} of ${questions.length}`;
    if (ptsElem) ptsElem.textContent = `${q.points} pt${q.points > 1 ? 's' : ''}`;
    
    if (typeElem) {
      const typeNames = {
        'MCQ_SINGLE': 'Single-Choice MCQ',
        'MCQ_MULTIPLE': 'Multiple-Choice (Multi-Select)',
        'IMAGE_MCQ': 'Diagrammatic Spotter',
        'SHORT_ANSWER': 'Short Conceptual Answer',
        'LONG_ESSAY': 'Structured Essay Response',
        'ESSAY': 'Structured Essay Response',
        'CODING': 'Code Synthesis'
      };
      typeElem.textContent = typeNames[q.question_type] || q.question_type;
    }

    if (promptElem) {
      promptElem.innerHTML = q.prompt;
    }

    // Handle Image MCQ
    const imgContainer = document.getElementById('question-image-container');
    const imgElement = document.getElementById('question-diagram-img');
    if (q.image_url && imgContainer && imgElement) {
      imgElement.src = q.image_url;
      imgContainer.style.display = 'block';
    } else if (imgContainer) {
      imgContainer.style.display = 'none';
    }

    // Update Bookmark button text and active state
    updateBookmarkButtonState(q.answer ? q.answer.is_bookmarked : false);

    // Render Answer Area based on type
    const mcqArea = document.getElementById('mcq-options-area');
    const textAnswerArea = document.getElementById('text-answer-area');
    const wordCounterWrap = document.getElementById('word-counter-wrapper');

    if (['MCQ_SINGLE', 'MCQ_MULTIPLE', 'IMAGE_MCQ'].includes(q.question_type)) {
      if (mcqArea) mcqArea.style.display = 'flex';
      if (textAnswerArea) textAnswerArea.style.display = 'none';
      if (wordCounterWrap) wordCounterWrap.style.display = 'none';
      renderMCQOptions(q);
    } else {
      if (mcqArea) mcqArea.style.display = 'none';
      if (textAnswerArea) textAnswerArea.style.display = 'block';
      if (wordCounterWrap) wordCounterWrap.style.display = 'block';
      renderTextResponse(q);
    }

    // Update Palette Active Class
    document.querySelectorAll('.palette-tile').forEach((tile, tIdx) => {
      tile.classList.toggle('active', tIdx === index);
    });

    // Update Prev/Next buttons & Linear Progression Labels
    if (btnPrev) {
      btnPrev.disabled = index === 0;
      if (!config.allowBackNavigation) btnPrev.style.display = 'none';
    }
    if (btnNext) {
      const isLast = index === questions.length - 1;
      const nextBtnSpan = btnNext.querySelector('span');
      if (nextBtnSpan) {
        if (isLast) {
          nextBtnSpan.textContent = 'Save & Review Submission';
        } else if (!config.allowBackNavigation) {
          nextBtnSpan.textContent = 'Save Answer & Next';
        } else {
          nextBtnSpan.textContent = 'Next Question';
        }
      }
      btnNext.disabled = false; // Always allow clicking to trigger validation or progression
    }


    // Persist current question index position across page reloads
    try {
      localStorage.setItem(`optiexam_current_q_${config.attemptId}`, String(index));
    } catch (e) {
      console.warn('LocalStorage save failed:', e);
    }

    // Inform heartbeat about active question navigation
    heartbeat.queueAnswer(q.question_id, {});
  }


  function updateBookmarkButtonState(isBookmarked) {
    if (!btnBookmark) return;
    btnBookmark.classList.toggle('active', !!isBookmarked);
    if (bookmarkBtnText) {
      bookmarkBtnText.textContent = isBookmarked ? '★ Flagged for Review' : 'Flag for Review';
    }
  }

  function renderMCQOptions(q) {
    const container = document.getElementById('mcq-options-area');
    if (!container) return;
    container.innerHTML = '';

    const isMultiple = q.question_type === 'MCQ_MULTIPLE';
    const letters = ['A', 'B', 'C', 'D', 'E', 'F'];

    q.options.forEach((opt, optIdx) => {
      const card = document.createElement('div');
      const isSelected = q.answer.selected_option_ids.includes(opt.id);
      card.className = `option-card ${isSelected ? 'selected' : ''}`;
      card.id = `option-card-${opt.id}`;
      card.innerHTML = `
        <div class="option-letter">${letters[optIdx] || optIdx + 1}</div>
        <div class="option-text" style="flex: 1;">${opt.text}</div>
      `;

      card.addEventListener('click', () => {
        if (isMultiple) {
          if (q.answer.selected_option_ids.includes(opt.id)) {
            q.answer.selected_option_ids = q.answer.selected_option_ids.filter(id => id !== opt.id);
            card.classList.remove('selected');
          } else {
            q.answer.selected_option_ids.push(opt.id);
            card.classList.add('selected');
          }
        } else {
          q.answer.selected_option_ids = [opt.id];
          container.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
          card.classList.add('selected');
        }

        q.answer.is_answered = q.answer.selected_option_ids.length > 0;
        updatePaletteTileStatus(currentQuestionIndex, q.answer);
        updateGlobalStatsHUD();
        heartbeat.queueAnswer(q.question_id, { selected_option_ids: q.answer.selected_option_ids });
      });

      container.appendChild(card);
    });
  }

  function renderTextResponse(q) {
    const wordCountSpan = document.getElementById('word-count-num');
    const limitSpan = document.getElementById('word-limit-max');

    if (q.word_limit && limitSpan) {
      limitSpan.textContent = `/ ${q.word_limit} words max`;
    } else if (limitSpan) {
      limitSpan.textContent = '';
    }

    if (quillInstance) {
      isUpdatingQuillProgrammatically = true;
      const content = (q.answer && q.answer.text_response) ? q.answer.text_response : '';

      if (content && (content.includes('<p>') || content.includes('<h') || content.includes('<ul') || content.includes('<ol'))) {
        quillInstance.root.innerHTML = content;
      } else if (content) {
        quillInstance.setText(content);
      } else {
        quillInstance.setText('');
      }

      const text = quillInstance.getText().trim();
      const count = text ? text.split(/\s+/).filter(Boolean).length : 0;
      if (wordCountSpan) wordCountSpan.textContent = count;
      isUpdatingQuillProgrammatically = false;
    }

  }


  function updatePaletteTileStatus(idx, answer) {
    const tile = document.getElementById(`palette-tile-${idx}`);
    if (!tile) return;

    tile.classList.toggle('answered', !!answer.is_answered);
    tile.classList.toggle('bookmarked', !!answer.is_bookmarked);
    tile.classList.toggle('skipped', !!answer.is_skipped);

    let flagDot = tile.querySelector('.tile-flag-dot');
    if (answer.is_bookmarked && !flagDot) {
      flagDot = document.createElement('span');
      flagDot.className = 'tile-flag-dot';
      tile.appendChild(flagDot);
    } else if (!answer.is_bookmarked && flagDot) {
      flagDot.remove();
    }
  }

  function updateGlobalStatsHUD() {
    let answeredCount = 0;
    let bookmarkedCount = 0;

    questions.forEach(q => {
      if (q.answer && q.answer.is_answered) answeredCount += 1;
      if (q.answer && q.answer.is_bookmarked) bookmarkedCount += 1;
    });

    const remainingCount = questions.length - answeredCount;
    const percent = Math.round((answeredCount / questions.length) * 100) || 0;

    const ansElem = document.getElementById('stat-answered-count');
    const bkmElem = document.getElementById('stat-bookmarked-count');
    const remElem = document.getElementById('stat-remaining-count');
    const pctElem = document.getElementById('hudProgressPercent');
    const fillElem = document.getElementById('hudProgressFill');

    if (ansElem) ansElem.textContent = answeredCount;
    if (bkmElem) bkmElem.textContent = bookmarkedCount;
    if (remElem) remElem.textContent = remainingCount;
    if (pctElem) pctElem.textContent = `${percent}%`;
    if (fillElem) fillElem.style.width = `${percent}%`;

    // Update filter counts
    const fAll = document.getElementById('filter-cnt-all');
    const fAns = document.getElementById('filter-cnt-ans');
    const fUnans = document.getElementById('filter-cnt-unans');
    const fFlag = document.getElementById('filter-cnt-flag');
    if (fAll) fAll.textContent = questions.length;
    if (fAns) fAns.textContent = answeredCount;
    if (fUnans) fUnans.textContent = remainingCount;
    if (fFlag) fFlag.textContent = bookmarkedCount;
  }

  // Palette Filter Logic (All, Answered, Unanswered, Flagged)
  let activePaletteFilter = 'all';
  document.querySelectorAll('.palette-filter-bar .filter-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.palette-filter-bar .filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      activePaletteFilter = chip.getAttribute('data-filter') || 'all';
      applyPaletteFilter();
    });
  });

  function applyPaletteFilter() {
    questions.forEach((q, idx) => {
      const tile = document.getElementById(`palette-tile-${idx}`);
      if (!tile) return;

      let visible = true;
      if (activePaletteFilter === 'answered') {
        visible = !!(q.answer && q.answer.is_answered);
      } else if (activePaletteFilter === 'unanswered') {
        visible = !(q.answer && q.answer.is_answered);
      } else if (activePaletteFilter === 'flagged') {
        visible = !!(q.answer && q.answer.is_bookmarked);
      }
      tile.style.display = visible ? 'flex' : 'none';
    });
  }

  // Low-Time Web Audio Chime Synthesizer (Zero asset dependency)
  let playedWarningBeep = false;
  let playedDangerBeep = false;

  function playSoftAlertTone(freq = 440, duration = 0.25) {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      console.warn('Audio tone could not play:', e);
    }
  }

  function updateTimerDisplay(seconds) {
    const timerElem = document.getElementById('cockpit-timer-digits');
    const timerBox = document.getElementById('cockpit-timer-box');
    if (!timerElem) return;

    if (seconds <= 0) {
      timerElem.textContent = '00:00:00';
      return;
    }

    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    const formatted = `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    timerElem.textContent = formatted;

    if (timerBox) {
      const isWarning = seconds <= 300 && seconds > 60;
      const isDanger = seconds <= 60;

      timerBox.classList.toggle('warning', isWarning);
      timerBox.classList.toggle('danger', isDanger);

      if (isWarning && !playedWarningBeep) {
        playSoftAlertTone(523.25, 0.4); // C5 tone
        playedWarningBeep = true;
      }
      if (isDanger && !playedDangerBeep) {
        playSoftAlertTone(659.25, 0.6); // E5 tone
        playedDangerBeep = true;
      }
    }
  }


  function handleExamExpired() {
    const expiryModal = document.getElementById('time-expiry-modal');
    if (expiryModal) {
      expiryModal.classList.add('show');
    }
    setTimeout(() => {
      window.location.href = config.submitUrl;
    }, 2000);
  }

  // 14. Lifeline Actions
  // 50:50 Eliminator
  if (btnFiftyFifty) {
    btnFiftyFifty.addEventListener('click', async () => {
      const q = questions[currentQuestionIndex];
      if (!q) return;

      try {
        const resp = await fetch(config.lifelineUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': config.csrfToken },
          body: JSON.stringify({ lifeline_type: 'FIFTY_FIFTY', question_id: q.question_id })
        });
        const data = await resp.json();
        if (data.success && data.data.eliminated_option_ids) {
          data.data.eliminated_option_ids.forEach(optId => {
            const card = document.getElementById(`option-card-${optId}`);
            if (card) card.classList.add('eliminated');
          });
          btnFiftyFifty.disabled = data.remaining_quota <= 0;
          btnFiftyFifty.querySelector('span').textContent = `50:50 (${data.remaining_quota})`;
        } else {
          await showCockpitDialog('Lifeline Notice', data.error || 'Lifeline could not be applied to this question.');
        }
      } catch (err) {
        console.warn(err);
      }
    });
  }

  // Hint Token
  if (btnHint) {
    btnHint.addEventListener('click', async () => {
      const q = questions[currentQuestionIndex];
      if (!q) return;

      try {
        const resp = await fetch(config.lifelineUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': config.csrfToken },
          body: JSON.stringify({ lifeline_type: 'HINT_TOKEN', question_id: q.question_id })
        });
        const data = await resp.json();
        if (data.success && data.data.hint_text) {
          if (hintContent) hintContent.textContent = data.data.hint_text;
          if (hintModal) hintModal.classList.add('show');
          btnHint.disabled = data.remaining_quota <= 0;
          btnHint.querySelector('span').textContent = `Hint (${data.remaining_quota})`;
        } else {
          await showCockpitDialog('Hint Unavailable', data.error || 'No guidance hint has been configured for this question.');
        }
      } catch (err) {
        console.warn(err);
      }
    });
  }

  // Close Hint Modal
  if (btnCloseHint && hintModal) {
    btnCloseHint.addEventListener('click', () => hintModal.classList.remove('show'));
  }
  if (btnDismissHint && hintModal) {
    btnDismissHint.addEventListener('click', () => hintModal.classList.remove('show'));
  }

  // 15. Fullscreen Return Action
  if (btnReturnFullscreen) {
    btnReturnFullscreen.addEventListener('click', () => {
      document.documentElement.requestFullscreen().catch(e => console.warn(e));
    });
  }

  // 16. Scientific & Standard Calculator Controller
  const btnOpenCalc = document.getElementById('btn-open-calc');
  const calcModal = document.getElementById('calculator-modal-overlay');
  const btnCloseCalc = document.getElementById('btn-close-calc-modal');
  const btnToggleCalcMode = document.getElementById('btn-toggle-calc-mode');
  const calcKeypad = document.getElementById('calcKeypad');
  const calcMainDisplay = document.getElementById('calc-main-display');
  const calcHistDisplay = document.getElementById('calc-history-display');

  if (btnOpenCalc && calcModal) {
    btnOpenCalc.addEventListener('click', () => calcModal.classList.add('show'));
  }
  if (btnCloseCalc && calcModal) {
    btnCloseCalc.addEventListener('click', () => calcModal.classList.remove('show'));
  }

  let calcCurrentExpr = '';
  let calcLastAnswer = 0;
  let isScientificMode = true;

  if (btnToggleCalcMode && calcKeypad) {
    btnToggleCalcMode.addEventListener('click', () => {
      isScientificMode = !isScientificMode;
      btnToggleCalcMode.textContent = isScientificMode ? 'Scientific' : 'Standard';
      calcKeypad.classList.toggle('standard-mode', !isScientificMode);
    });
  }

  function updateCalcScreen(val = null) {
    if (calcMainDisplay) {
      calcMainDisplay.textContent = val !== null ? val : (calcCurrentExpr || '0');
    }
  }

  if (calcKeypad) {
    calcKeypad.addEventListener('click', (e) => {
      const btn = e.target.closest('.calc-btn');
      if (!btn) return;

      const num = btn.getAttribute('data-num');
      const op = btn.getAttribute('data-op');
      const action = btn.getAttribute('data-action');

      if (num !== null) {
        if (calcCurrentExpr === '0' && num !== '.') calcCurrentExpr = num;
        else calcCurrentExpr += num;
        updateCalcScreen();
      } else if (action === 'clear') {
        calcCurrentExpr = '';
        if (calcHistDisplay) calcHistDisplay.innerHTML = '&nbsp;';
        updateCalcScreen('0');
      } else if (action === 'backspace') {
        calcCurrentExpr = calcCurrentExpr.slice(0, -1);
        updateCalcScreen(calcCurrentExpr || '0');
      } else if (action === 'equals') {
        if (!calcCurrentExpr) return;
        try {
          if (calcHistDisplay) calcHistDisplay.textContent = `${calcCurrentExpr} =`;
          let evalExpr = calcCurrentExpr
            .replace(/×/g, '*')
            .replace(/÷/g, '/')
            .replace(/−/g, '-')
            .replace(/π/g, 'Math.PI')
            .replace(/e/g, 'Math.E');

          // Safe math evaluation
          const result = Function(`'use strict'; return (${evalExpr})`)();
          calcLastAnswer = Number(result);
          calcCurrentExpr = String(Math.round(result * 100000000) / 100000000);
          updateCalcScreen(calcCurrentExpr);
        } catch (err) {
          updateCalcScreen('Error');
          calcCurrentExpr = '';
        }
      } else if (op) {
        switch (op) {
          case 'sin':
          case 'cos':
          case 'tan':
          case 'log':
          case 'sqrt':
            try {
              let currentVal = parseFloat(calcCurrentExpr) || calcLastAnswer || 0;
              let res = 0;
              if (op === 'sin') res = Math.sin((currentVal * Math.PI) / 180);
              else if (op === 'cos') res = Math.cos((currentVal * Math.PI) / 180);
              else if (op === 'tan') res = Math.tan((currentVal * Math.PI) / 180);
              else if (op === 'log') res = Math.log10(currentVal);
              else if (op === 'sqrt') res = Math.sqrt(currentVal);

              if (calcHistDisplay) calcHistDisplay.textContent = `${op}(${currentVal}) =`;
              calcLastAnswer = res;
              calcCurrentExpr = String(Math.round(res * 100000000) / 100000000);
              updateCalcScreen(calcCurrentExpr);
            } catch (err) {
              updateCalcScreen('Error');
            }
            break;
          case 'ln':
            try {
              let currentVal = parseFloat(calcCurrentExpr) || 0;
              let res = Math.log(currentVal);
              calcCurrentExpr = String(Math.round(res * 100000000) / 100000000);
              updateCalcScreen(calcCurrentExpr);
            } catch (e) { updateCalcScreen('Error'); }
            break;
          case 'pow':
            try {
              let currentVal = parseFloat(calcCurrentExpr) || 0;
              let res = Math.pow(currentVal, 2);
              calcCurrentExpr = String(res);
              updateCalcScreen(calcCurrentExpr);
            } catch (e) { updateCalcScreen('Error'); }
            break;
          case 'inv':
            try {
              let currentVal = parseFloat(calcCurrentExpr) || 0;
              let res = 1 / currentVal;
              calcCurrentExpr = String(Math.round(res * 100000000) / 100000000);
              updateCalcScreen(calcCurrentExpr);
            } catch (e) { updateCalcScreen('Error'); }
            break;
          case 'neg':
            if (calcCurrentExpr.startsWith('-')) calcCurrentExpr = calcCurrentExpr.slice(1);
            else if (calcCurrentExpr) calcCurrentExpr = '-' + calcCurrentExpr;
            updateCalcScreen();
            break;
          case 'pi':
            calcCurrentExpr += Math.PI.toFixed(6);
            updateCalcScreen();
            break;
          case 'ans':
            calcCurrentExpr += String(calcLastAnswer);
            updateCalcScreen();
            break;
          default:
            calcCurrentExpr += ` ${op} `;
            updateCalcScreen();
        }
      }
    });
  }
});




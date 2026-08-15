/**
 * OptiExam Interactive Examination Cockpit Controller
 * Clean, Robust, Modular Execution
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!window.COCKPIT_CONFIG) return;

  const config = window.COCKPIT_CONFIG;
  let currentQuestionIndex = 0;
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
  const btnSkip = document.getElementById('btn-lifeline-skip');
  const hintModal = document.getElementById('lifeline-hint-modal');
  const hintContent = document.getElementById('lifeline-hint-content');
  const btnCloseHint = document.getElementById('btn-close-hint-modal');
  const btnDismissHint = document.getElementById('btn-dismiss-hint');
  const btnReturnFullscreen = document.getElementById('btn-return-fullscreen');


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
  const antiCheat = new AntiCheatShield({
    enforceFullscreen: config.enforceFullscreen,
    lockCopyPaste: config.lockCopyPaste,
    maxViolations: config.maxViolations || 3,
    onViolation: (type, message, count) => {
      const countBadge = document.getElementById('violation-counter-pill');
      const countText = document.getElementById('violation-count-text');
      if (countBadge && count > 0) {
        countBadge.style.display = 'inline-flex';
        if (countText) countText.textContent = `${count} Violation${count > 1 ? 's' : ''}`;
      }

      fetch(config.violationUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': config.csrfToken
        },
        body: JSON.stringify({ event_type: type, details: { message } })
      }).catch(e => console.warn(e));
    }
  });

  // 4. Theme Toggle Button
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

  // 5. Initial Stats & Initial Question Render
  updateGlobalStatsHUD();
  renderQuestion(currentQuestionIndex);

  // 6. Navigation Buttons
  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentQuestionIndex > 0) {
        currentQuestionIndex -= 1;
        renderQuestion(currentQuestionIndex);
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex += 1;
        renderQuestion(currentQuestionIndex);
      }
    });
  }

  // 7. Bind Palette Tiles
  document.querySelectorAll('.palette-tile').forEach((tile) => {
    tile.addEventListener('click', () => {
      const idx = parseInt(tile.getAttribute('data-index'), 10);
      if (!isNaN(idx) && idx >= 0 && idx < questions.length) {
        currentQuestionIndex = idx;
        renderQuestion(currentQuestionIndex);
      }
    });
  });

  // 8. Bookmark / Flag Toggle Button
  if (btnBookmark) {
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

  // 9. Clear Answer Button
  if (btnClear) {
    btnClear.addEventListener('click', () => {
      const q = questions[currentQuestionIndex];
      if (!q) return;

      if (['MCQ_SINGLE', 'MCQ_MULTIPLE', 'IMAGE_MCQ'].includes(q.question_type)) {
        q.answer.selected_option_ids = [];
        const container = document.getElementById('mcq-options-area');
        if (container) {
          container.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
        }
      } else {
        q.answer.text_response = '';
        const textarea = document.getElementById('question-text-response');
        if (textarea) textarea.value = '';
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

  // 10. Rich Text Formatting Toolbar Handlers
  const richToolbar = document.getElementById('richTextToolbar');
  if (richToolbar) {
    richToolbar.querySelectorAll('.toolbar-btn[data-format]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const format = btn.getAttribute('data-format');
        const textarea = document.getElementById('question-text-response');
        if (!textarea) return;

        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selected = textarea.value.substring(start, end);
        let replacement = '';

        switch (format) {
          case 'bold':
            replacement = `**${selected || 'bold text'}**`;
            break;
          case 'italic':
            replacement = `*${selected || 'italic text'}*`;
            break;
          case 'underline':
            replacement = `<u>${selected || 'underlined text'}</u>`;
            break;
          case 'strike':
            replacement = `~~${selected || 'strikethrough text'}~~`;
            break;
          case 'heading':
            replacement = `\n### ${selected || 'Section Heading'}\n`;
            break;
          case 'bullet':
            replacement = `\n- ${selected || 'List item'}`;
            break;
          case 'number':
            replacement = `\n1. ${selected || 'Numbered item'}`;
            break;
          case 'code':
            replacement = `\`\`\`\n${selected || '// code block'}\n\`\`\``;
            break;
          case 'quote':
            replacement = `\n> ${selected || 'Quotation text'}\n`;
            break;
          case 'table':
            replacement = `\n| Column 1 | Column 2 | Column 3 |\n| :--- | :--- | :--- |\n| Value A | Value B | Value C |\n`;
            break;
          case 'math':
            replacement = `$${selected || 'E = mc^2'}$`;
            break;
          default:
            replacement = selected;
        }


        textarea.setRangeText(replacement, start, end, 'end');
        textarea.focus();
        textarea.dispatchEvent(new Event('input'));
      });
    });

    const btnClearEditor = document.getElementById('btn-clear-editor-text');
    if (btnClearEditor) {
      btnClearEditor.addEventListener('click', () => {
        const textarea = document.getElementById('question-text-response');
        if (textarea && confirm('Clear all content from this answer box?')) {
          textarea.value = '';
          textarea.dispatchEvent(new Event('input'));
        }
      });
    }
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
      if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex += 1;
        renderQuestion(currentQuestionIndex);
      }
    } else if (e.altKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      if (currentQuestionIndex > 0) {
        currentQuestionIndex -= 1;
        renderQuestion(currentQuestionIndex);
      }
    } else if (e.altKey && (e.key === 'f' || e.key === 'F')) {
      e.preventDefault();
      if (btnBookmark) btnBookmark.click();
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

    // Update Prev/Next buttons
    if (btnPrev) {
      btnPrev.disabled = index === 0;
    }
    if (btnNext) {
      btnNext.disabled = index === questions.length - 1;
    }
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
    const textarea = document.getElementById('question-text-response');
    const wordCountSpan = document.getElementById('word-count-num');
    const limitSpan = document.getElementById('word-limit-max');
    if (!textarea) return;

    textarea.value = q.answer.text_response || '';

    if (q.word_limit && limitSpan) {
      limitSpan.textContent = `/ ${q.word_limit} words max`;
    } else if (limitSpan) {
      limitSpan.textContent = '';
    }

    const updateCount = () => {
      const text = textarea.value.trim();
      const count = text ? text.split(/\s+/).length : 0;
      if (wordCountSpan) wordCountSpan.textContent = count;

      q.answer.text_response = textarea.value;
      q.answer.is_answered = count > 0;
      updatePaletteTileStatus(currentQuestionIndex, q.answer);
      updateGlobalStatsHUD();
      heartbeat.queueAnswer(q.question_id, { text_response: textarea.value });
    };

    textarea.oninput = updateCount;
    updateCount();
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
      timerBox.classList.toggle('warning', seconds <= 300 && seconds > 60);
      timerBox.classList.toggle('danger', seconds <= 60);
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
          alert(data.error || 'Lifeline failed.');
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
          alert(data.error || 'No guidance hint configured for this question.');
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

  // Skip Question Lifeline
  if (btnSkip) {
    btnSkip.addEventListener('click', async () => {
      const q = questions[currentQuestionIndex];
      if (!q) return;

      if (!confirm('Use Skip Question lifeline on this question? You can return to it later.')) return;

      try {
        const resp = await fetch(config.lifelineUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': config.csrfToken },
          body: JSON.stringify({ lifeline_type: 'SKIP_QUESTION', question_id: q.question_id })
        });
        const data = await resp.json();
        if (data.success) {
          q.answer.is_skipped = true;
          updatePaletteTileStatus(currentQuestionIndex, q.answer);
          btnSkip.disabled = data.remaining_quota <= 0;
          btnSkip.querySelector('span').textContent = `Skip (${data.remaining_quota})`;
          // Advance to next question if available
          if (currentQuestionIndex < questions.length - 1) {
            currentQuestionIndex += 1;
            renderQuestion(currentQuestionIndex);
          }
        } else {
          alert(data.error || 'Skip lifeline failed.');
        }
      } catch (err) {
        console.warn(err);
      }
    });
  }

  // 15. Fullscreen Return Action
  if (btnReturnFullscreen) {
    btnReturnFullscreen.addEventListener('click', () => {
      document.documentElement.requestFullscreen().catch(e => console.warn(e));
    });
  }
});


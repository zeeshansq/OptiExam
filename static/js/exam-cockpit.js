/**
 * OptiExam Interactive Examination Cockpit Controller
 * Question navigation palette, answer triggers, lifeline executions, word limits, and submit modals.
 */

document.addEventListener('DOMContentLoaded', () => {
  if (!window.COCKPIT_CONFIG) return;

  const config = window.COCKPIT_CONFIG;
  let currentQuestionIndex = 0;
  const questions = config.questions;

  // Initialize Heartbeat Sync
  const heartbeat = new HeartbeatSyncEngine({
    attemptId: config.attemptId,
    heartbeatUrl: config.heartbeatUrl,
    csrfToken: config.csrfToken,
    remainingSeconds: config.remainingSeconds,
    onTick: (seconds) => updateTimerDisplay(seconds),
    onExpired: () => handleExamExpired()
  });

  // Initialize Anti-Cheat Shield
  const antiCheat = new AntiCheatShield({
    enforceFullscreen: config.enforceFullscreen,
    lockCopyPaste: config.lockCopyPaste,
    maxViolations: config.maxViolations || 3,
    onViolation: (type, message, count) => {
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

  // Render Initial Question
  renderQuestion(currentQuestionIndex);

  // Bind Navigation Buttons
  const btnPrev = document.getElementById('btn-prev-question');
  const btnNext = document.getElementById('btn-next-question');
  const btnSubmitModal = document.getElementById('btn-submit-exam');

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

  // Bind Palette Tiles
  document.querySelectorAll('.palette-tile').forEach((tile) => {
    tile.addEventListener('click', () => {
      const idx = parseInt(tile.getAttribute('data-index'), 10);
      if (!isNaN(idx) && idx >= 0 && idx < questions.length) {
        currentQuestionIndex = idx;
        renderQuestion(currentQuestionIndex);
      }
    });
  });

  function renderQuestion(index) {
    const q = questions[index];
    if (!q) return;

    // Update Meta info
    document.getElementById('current-question-num').textContent = `Question ${q.order} of ${questions.length}`;
    document.getElementById('current-question-points').textContent = `${q.points} pt${q.points > 1 ? 's' : ''}`;
    document.getElementById('current-question-prompt').innerHTML = q.prompt;

    // Handle Image MCQ
    const imgContainer = document.getElementById('question-image-container');
    const imgElement = document.getElementById('question-diagram-img');
    if (q.image_url && imgContainer && imgElement) {
      imgElement.src = q.image_url;
      imgContainer.style.display = 'block';
    } else if (imgContainer) {
      imgContainer.style.display = 'none';
    }

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
    if (btnPrev) btnPrev.disabled = index === 0;
    if (btnNext) btnNext.disabled = index === questions.length - 1;
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
        <div class="option-text" style="flex: 1; font-size: 0.95rem;">${opt.text}</div>
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
      heartbeat.queueAnswer(q.question_id, { text_response: textarea.value });
    };

    textarea.oninput = updateCount;
    updateCount();
  }

  function updatePaletteTileStatus(idx, answer) {
    const tile = document.querySelector(`.palette-tile[data-index="${idx}"]`);
    if (!tile) return;

    tile.classList.toggle('answered', answer.is_answered);
    tile.classList.toggle('bookmarked', answer.is_bookmarked);
    tile.classList.toggle('skipped', answer.is_skipped);
  }

  function updateTimerDisplay(seconds) {
    const timerElem = document.getElementById('cockpit-timer-digits');
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

    timerElem.classList.toggle('warning', seconds <= 300 && seconds > 60);
    timerElem.classList.toggle('danger', seconds <= 60);
  }

  function handleExamExpired() {
    alert('Time has expired! Submitting your examination.');
    window.location.href = config.submitUrl;
  }

  // Lifeline Actions
  const btnFiftyFifty = document.getElementById('btn-lifeline-fifty');
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
        } else {
          alert(data.error || 'Lifeline failed.');
        }
      } catch (err) {
        console.warn(err);
      }
    });
  }

  // Fullscreen return button
  const btnReturnFullscreen = document.getElementById('btn-return-fullscreen');
  if (btnReturnFullscreen) {
    btnReturnFullscreen.addEventListener('click', () => {
      document.documentElement.requestFullscreen().catch(e => console.warn(e));
    });
  }
});

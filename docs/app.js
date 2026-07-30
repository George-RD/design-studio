    const command = document.querySelector('[data-copy]');
    const status = document.getElementById('copy-status');

    async function copyText(value) {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
        return;
      }
      const textarea = document.createElement('textarea');
      textarea.value = value;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      try {
        textarea.select();
        if (!document.execCommand('copy')) {
          throw new Error('copy command rejected');
        }
      } finally {
        textarea.remove();
      }
    }

    command?.addEventListener('click', async () => {
      const value = command.dataset.copy || '';
      const label = command.querySelector('.command__copy');
      try {
        await copyText(value);
        label.textContent = 'Copied';
        status.textContent = 'Command copied.';
      } catch {
        label.textContent = 'Select text';
        status.textContent = 'Copy was blocked. Select the command text manually.';
      }
      window.setTimeout(() => { label.textContent = 'Copy command'; }, 1800);
    });

    const handoffDemo = document.querySelector('[data-handoff-demo]');

    if (handoffDemo) {
      const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
      const toggle = handoffDemo.querySelector('[data-demo-toggle]');
      const packet = handoffDemo.querySelector('[data-demo-packet]');
      const demoStatus = handoffDemo.querySelector('[data-demo-status]');
      const browserState = handoffDemo.querySelector('[data-browser-state]');
      const stepButtons = [...handoffDemo.querySelectorAll('[data-demo-step]')];
      const steps = [
        { status: '01 / Frame product truth', packet: 'Truth', browser: 'Waiting' },
        { status: '02 / Direct without source', packet: 'Brief', browser: 'Waiting' },
        { status: '03 / Build the contract', packet: 'Contract', browser: 'Serving' },
        { status: '04 / Judge in browser', packet: 'Evidence', browser: 'Verified' },
        { status: '05 / Select from evidence', packet: 'Build 03', browser: 'Accepted' },
      ];

      let currentStep = 0;
      let paused = reduceMotion.matches;
      let inView = true;
      let timer = null;

      function renderStep(nextStep) {
        currentStep = (nextStep + steps.length) % steps.length;
        const step = steps[currentStep];
        handoffDemo.dataset.step = String(currentStep);
        demoStatus.textContent = step.status;
        packet.textContent = step.packet;
        browserState.textContent = step.browser;
        stepButtons.forEach((button, index) => {
          if (index === currentStep) button.setAttribute('aria-current', 'step');
          else button.removeAttribute('aria-current');
        });
      }

      function updateToggle() {
        const isPaused = paused || reduceMotion.matches;
        toggle.textContent = isPaused ? 'Play' : 'Pause';
        toggle.setAttribute('aria-label', isPaused ? 'Play workflow animation' : 'Pause workflow animation');
      }

      function stopTimer() {
        if (timer !== null) window.clearTimeout(timer);
        timer = null;
      }

      function scheduleNext() {
        stopTimer();
        if (paused || reduceMotion.matches || !inView || document.hidden) return;
        timer = window.setTimeout(() => {
          renderStep(currentStep + 1);
          scheduleNext();
        }, 2400);
      }

      toggle.addEventListener('click', () => {
        paused = !paused;
        updateToggle();
        scheduleNext();
      });

      stepButtons.forEach((button) => {
        button.addEventListener('click', () => {
          paused = true;
          renderStep(Number(button.dataset.demoStep));
          updateToggle();
          scheduleNext();
        });
      });

      reduceMotion.addEventListener('change', () => {
        if (reduceMotion.matches) paused = true;
        updateToggle();
        scheduleNext();
      });

      document.addEventListener('visibilitychange', scheduleNext);

      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          inView = entries[0]?.isIntersecting ?? true;
          scheduleNext();
        }, { threshold: 0.25 });
        observer.observe(handoffDemo);
      }

      renderStep(0);
      updateToggle();
      scheduleNext();
    }

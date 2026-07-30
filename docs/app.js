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

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function createAutoSequence({
  root,
  toggle,
  buttons,
  length,
  delay,
  render,
  playLabel,
  pauseLabel,
}) {
  let currentStep = 0;
  let paused = reduceMotion.matches;
  let inView = true;
  let timer = null;

  function updateToggle() {
    const isPaused = paused || reduceMotion.matches;
    toggle.textContent = isPaused ? 'Play' : 'Pause';
    toggle.setAttribute('aria-label', isPaused ? playLabel : pauseLabel);
  }

  function stopTimer() {
    if (timer !== null) window.clearTimeout(timer);
    timer = null;
  }

  function scheduleNext() {
    stopTimer();
    if (paused || reduceMotion.matches || !inView || document.hidden) return;

    timer = window.setTimeout(() => {
      currentStep = (currentStep + 1) % length;
      render(currentStep, false);
      scheduleNext();
    }, delay);
  }

  function chooseStep(nextStep, userInitiated = false) {
    currentStep = (nextStep + length) % length;
    render(currentStep, userInitiated);
    if (userInitiated) paused = true;
    updateToggle();
    scheduleNext();
  }

  toggle.addEventListener('click', () => {
    paused = !paused;
    updateToggle();
    scheduleNext();
  });

  buttons.forEach((button) => {
    button.addEventListener('click', () => chooseStep(Number(button.dataset.sequenceStep), true));
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
    observer.observe(root);
  }

  chooseStep(0);
}

const heroRun = document.querySelector('[data-hero-run]');

if (heroRun) {
  const toggle = heroRun.querySelector('[data-hero-toggle]');
  const heroStatus = heroRun.querySelector('[data-hero-status]');
  const panel = heroRun.querySelector('.hero-run__panel');
  const title = heroRun.querySelector('[data-hero-title]');
  const tag = heroRun.querySelector('[data-hero-tag]');
  const room = heroRun.querySelector('[data-hero-room]');
  const copy = heroRun.querySelector('[data-hero-copy]');
  const from = heroRun.querySelector('[data-hero-from]');
  const to = heroRun.querySelector('[data-hero-to]');
  const result = heroRun.querySelector('[data-hero-result]');
  const stepButtons = [...heroRun.querySelectorAll('[data-hero-step]')];

  stepButtons.forEach((button, index) => {
    button.dataset.sequenceStep = button.dataset.heroStep;
    button.addEventListener('keydown', (event) => {
      const keyTargets = {
        ArrowRight: (index + 1) % stepButtons.length,
        ArrowDown: (index + 1) % stepButtons.length,
        ArrowLeft: (index - 1 + stepButtons.length) % stepButtons.length,
        ArrowUp: (index - 1 + stepButtons.length) % stepButtons.length,
        Home: 0,
        End: stepButtons.length - 1,
      };
      if (!(event.key in keyTargets)) return;
      event.preventDefault();
      stepButtons[keyTargets[event.key]].focus();
      stepButtons[keyTargets[event.key]].click();
    });
  });

  const steps = [
    {
      status: '01 / Framing',
      title: 'Frame',
      tag: 'Rooted context',
      room: 'Source room',
      copy: 'Product truth, app root, constraints and proof become a small testable brief.',
      from: 'Product truth',
      to: 'Surface brief',
      result: 'Brief ready',
    },
    {
      status: '02 / Directing',
      title: 'Direct',
      tag: 'No source',
      room: 'Blind room',
      copy: 'The Visual Director creates one visual world without inheriting selectors, components or layout decisions.',
      from: 'Surface brief',
      to: 'Visual contract',
      result: 'Direction locked',
    },
    {
      status: '03 / Building',
      title: 'Build',
      tag: 'Source enabled',
      room: 'Source room',
      copy: 'The Builder turns the contract into working code, complete states and a preserved iteration.',
      from: 'Visual contract',
      to: 'Build 03',
      result: 'Iteration saved',
    },
    {
      status: '04 / Judging',
      title: 'Judge',
      tag: 'Browser blind',
      room: 'Blind room',
      copy: 'A fresh Evaluator uses the live page, tests interactions and records browser evidence.',
      from: 'Build 03',
      to: 'Observation',
      result: 'Evidence recorded',
    },
    {
      status: '05 / Selecting',
      title: 'Select',
      tag: 'Evidence first',
      room: 'Orchestrator',
      copy: 'The best eligible iteration wins. The latest build has no automatic advantage.',
      from: 'Build 03',
      to: 'Site + DNA + tokens',
      result: '03 accepted',
    },
  ];

  function renderHeroStep(nextStep, userInitiated) {
    const step = steps[nextStep];
    heroRun.dataset.step = String(nextStep);
    heroStatus.lastChild.textContent = step.status;
    title.textContent = step.title;
    tag.textContent = step.tag;
    room.textContent = step.room;
    copy.textContent = step.copy;
    from.textContent = step.from;
    to.textContent = step.to;
    result.textContent = step.result;

    stepButtons.forEach((button, index) => {
      const selected = index === nextStep;
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });

    if (!reduceMotion.matches && panel.animate) {
      panel.getAnimations().forEach((animation) => animation.cancel());
      panel.animate(
        [
          { opacity: 0.55, transform: 'translateY(10px)' },
          { opacity: 1, transform: 'translateY(0)' },
        ],
        { duration: userInitiated ? 260 : 420, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' },
      );
    }
  }

  createAutoSequence({
    root: heroRun,
    toggle,
    buttons: stepButtons,
    length: steps.length,
    delay: 3600,
    render: renderHeroStep,
    playLabel: 'Play run board animation',
    pauseLabel: 'Pause run board animation',
  });
}

const handoffDemo = document.querySelector('[data-handoff-demo]');

if (handoffDemo) {
  const toggle = handoffDemo.querySelector('[data-demo-toggle]');
  const packet = handoffDemo.querySelector('[data-demo-packet]');
  const demoStatus = handoffDemo.querySelector('[data-demo-status]');
  const browserState = handoffDemo.querySelector('[data-browser-state]');
  const browserGate = handoffDemo.querySelector('.browser-gate');
  const stepButtons = [...handoffDemo.querySelectorAll('[data-demo-step]')];

  stepButtons.forEach((button) => {
    button.dataset.sequenceStep = button.dataset.demoStep;
  });

  const steps = [
    { status: '01 / Frame product truth', packet: 'Truth', browser: 'Waiting', agent: 'planner' },
    { status: '02 / Direct without source', packet: 'Brief', browser: 'Waiting', agent: 'director' },
    { status: '03 / Build the contract', packet: 'Contract', browser: 'Serving', agent: 'builder' },
    { status: '04 / Judge in browser', packet: 'Evidence', browser: 'Verified', agent: 'evaluator' },
    { status: '05 / Select from evidence', packet: 'Build 03', browser: 'Accepted', agent: null },
  ];

  function movePacket(step) {
    const target = step.agent
      ? handoffDemo.querySelector(`[data-agent="${step.agent}"] > div`)
      : browserGate;

    if (!target) return;
    target.appendChild(packet);
    browserState.hidden = !step.agent;

    if (!reduceMotion.matches && packet.animate) {
      packet.getAnimations().forEach((animation) => animation.cancel());
      packet.animate(
        [
          { opacity: 0, transform: 'translateY(-8px) scale(0.96)' },
          { opacity: 1, transform: 'translateY(0) scale(1)' },
        ],
        { duration: 320, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' },
      );
    }
  }

  function renderHandoffStep(nextStep) {
    const step = steps[nextStep];
    handoffDemo.dataset.step = String(nextStep);
    demoStatus.textContent = step.status;
    packet.textContent = step.packet;
    browserState.textContent = step.browser;
    movePacket(step);

    stepButtons.forEach((button, index) => {
      if (index === nextStep) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
  }

  createAutoSequence({
    root: handoffDemo,
    toggle,
    buttons: stepButtons,
    length: steps.length,
    delay: 2400,
    render: renderHandoffStep,
    playLabel: 'Play workflow animation',
    pauseLabel: 'Pause workflow animation',
  });
}

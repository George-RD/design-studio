const twoFactor = document.querySelector('#two-factor');
const twoFactorStatus = document.querySelector('#two-factor-status');
const email = document.querySelector('#recovery-email');
const emailError = document.querySelector('#email-error');
const toast = document.querySelector('#toast');

twoFactor.addEventListener('click', () => {
  const enabled = twoFactor.getAttribute('aria-checked') !== 'true';
  twoFactor.setAttribute('aria-checked', String(enabled));
  twoFactorStatus.textContent = enabled ? 'On' : 'Off';
});

document.querySelector('#save-email').addEventListener('click', () => {
  if (!email.value.includes('@')) {
    emailError.textContent = 'Enter a valid email.';
    return;
  }

  emailError.textContent = '';
  toast.textContent = 'Recovery email saved.';
});

document.querySelector('#session-menu').addEventListener('click', () => {
  toast.textContent = 'Session actions would open here.';
});

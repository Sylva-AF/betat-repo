/* betat.js — bundled UI, progressive enhancement only.
 * BLUEPRINT §07 Decision Log, 2026-09-14: reverses the 2026-09-13
 * no-JS decision for exactly one case — a passphrase show/hide toggle,
 * which needs to read/mutate a real input's `type`, something pure CSS
 * cannot do (the checkbox-hack trick used elsewhere in this UI only
 * toggles visibility of static markup, never an input's live state).
 * Every form here already works correctly with this script disabled or
 * blocked; it only adds a convenience on top. No other JS ships in this
 * UI — keep it that way unless a future change gets the same explicit
 * sign-off this one did.
 */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input[type="password"]').forEach(function (input) {
    var wrap = document.createElement('span');
    wrap.className = 'bt-password-wrap';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'bt-password-toggle-btn';
    btn.textContent = 'Show';
    btn.setAttribute('aria-label', 'Show passphrase');
    btn.addEventListener('click', function () {
      var showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      btn.textContent = showing ? 'Show' : 'Hide';
      btn.setAttribute('aria-label', showing ? 'Show passphrase' : 'Hide passphrase');
    });
    wrap.appendChild(btn);
  });
});

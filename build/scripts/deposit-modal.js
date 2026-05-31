/**
 * Shadow Syndicate — Deposit Modal
 * Self-contained component. Include on any page with:
 *   <script src="../scripts/deposit-modal.js"></script>
 * Then open with: DepositModal.open()
 */
const DepositModal = (() => {
  const API_URL = SYNDICATE_API + '';
  let _info = null;

  function waddr() {
    const w = window.ShadowSyndicate?.wallet();
    return w?.connected ? w.address : null;
  }

  function inject() {
    if (document.getElementById('depositModal')) return;
    // Inject styles
    if (!document.getElementById('dmStyles')) {
      const css = `
      .deposit-modal{max-width:440px;width:90%;}
      .deposit-modal__body{padding:var(--space-4) var(--space-4) var(--space-4);}
      .deposit-step{display:flex;align-items:flex-start;gap:var(--space-3);margin-bottom:var(--space-3);}
      .deposit-step__num{width:22px;height:22px;border-radius:50%;background:rgba(45,212,191,0.12);color:var(--holo-teal);font-family:var(--font-mono);font-size:11px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
      .deposit-step__text{color:var(--text-secondary);font-size:var(--text-sm);padding-top:1px;}
      .deposit-addr{background:rgba(0,0,0,0.3);border:1px dashed var(--void-border);border-radius:var(--radius-md);padding:var(--space-3) var(--space-4);font-family:var(--font-mono);font-size:11px;color:var(--holo-teal);word-break:break-all;line-height:1.5;margin-bottom:var(--space-2);user-select:all;}
      .dm-copied{font-size:var(--text-xs);color:var(--state-success);opacity:0;transition:opacity .3s;margin-left:var(--space-3);}
      .dm-copied--show{opacity:1;}
      .dm-status{font-family:var(--font-mono);font-size:var(--text-xs);margin-top:var(--space-3);min-height:1.2em;}
      .dm-balance{font-family:var(--font-mono);font-size:var(--text-sm);color:var(--holo-purple);margin-top:var(--space-2);font-weight:700;}
      `;
      const s = document.createElement('style');
      s.id = 'dmStyles';
      s.textContent = css;
      document.head.appendChild(s);
    }
    const html = `
    <div class="modal-backdrop" id="depositModalBackdrop"></div>
    <div class="modal deposit-modal" id="depositModal">
      <div class="modal__header">
        <h3 class="modal__title">💎 Deposit $SHADE</h3>
        <button class="modal__close" id="depositModalClose">&times;</button>
      </div>
      <div class="deposit-modal__body">
        <div class="deposit-step">
          <div class="deposit-step__num">1</div>
          <div class="deposit-step__text">Send $SHADE from your wallet to:</div>
        </div>
        <div class="deposit-addr" id="dmAddr">Loading...</div>
        <button class="btn btn-cyan btn-sm" id="dmCopy" style="margin-bottom:var(--space-4);">📋 Copy Address</button>
        <span class="dm-copied" id="dmCopied">✓ Copied!</span>
        <div class="deposit-step">
          <div class="deposit-step__num">2</div>
          <div class="deposit-step__text">After sending, click Verify:</div>
        </div>
        <button class="btn btn-primary" id="dmVerify" style="width:100%;">🔍 Verify Deposit</button>
        <div class="dm-status" id="dmStatus"></div>
        <div class="dm-balance" id="dmBalance"></div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', html);
    bind();
  }

  function bind() {
    document.getElementById('depositModalClose').addEventListener('click', close);
    document.getElementById('depositModalBackdrop').addEventListener('click', close);
    document.getElementById('dmCopy').addEventListener('click', () => {
      const a = document.getElementById('dmAddr').textContent;
      if (a && a !== 'Loading...') {
        navigator.clipboard.writeText(a).then(() => {
          const el = document.getElementById('dmCopied');
          el.classList.add('dm-copied--show');
          setTimeout(() => el.classList.remove('dm-copied--show'), 2000);
        });
      }
    });
    document.getElementById('dmVerify').addEventListener('click', verify);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  async function load() {
    try {
      const r = await fetch(`${API_URL}/deposit/info`);
      _info = await r.json();
      document.getElementById('dmAddr').textContent =
        _info.casino_wallet || 'Not configured';
    } catch (e) {
      document.getElementById('dmAddr').textContent = 'Server offline';
    }
  }

  async function verify() {
    const a = waddr();
    if (!a) {
      document.getElementById('dmStatus').innerHTML = '<span style="color:var(--state-error);">Connect your wallet first</span>';
      return;
    }
    const st = document.getElementById('dmStatus');
    const bal = document.getElementById('dmBalance');
    st.innerHTML = '<span>⏳ Scanning blockchain...</span>';
    try {
      const r = await fetch(`${API_URL}/deposit/verify/${encodeURIComponent(a)}`);
      const d = await r.json();
      if (d.new_deposits?.length > 0) {
        const total = d.new_deposits.reduce((s, x) => s + x.shade_amount, 0);
        st.innerHTML = `<span style="color:var(--state-success);">+${total.toLocaleString()} $SHADE credited!</span>`;
      } else {
        st.innerHTML = '<span style="color:var(--text-muted);">No new deposits found. Send $SHADE first, then wait ~30s for confirmation.</span>';
      }
      bal.textContent = `Casino balance: ${d.balance_shade} $SHADE`;
    } catch (e) {
      st.innerHTML = '<span style="color:var(--state-error);">Server offline</span>';
    }
  }

  async function open() {
    inject();
    document.getElementById('depositModal').classList.add('active');
    document.getElementById('depositModalBackdrop').classList.add('active');
    document.body.style.overflow = 'hidden';
    await load();
    // Show current balance if wallet connected
    const a = waddr();
    if (a) {
      try {
        const r = await fetch(`${API_URL}/session/${encodeURIComponent(a)}`);
        const d = await r.json();
        document.getElementById('dmBalance').textContent =
          `Casino balance: ${d.balance_shade || '0'} $SHADE`;
      } catch (e) {}
    }
  }

  function close() {
    const m = document.getElementById('depositModal');
    const b = document.getElementById('depositModalBackdrop');
    if (m) m.classList.remove('active');
    if (b) b.classList.remove('active');
    document.body.style.overflow = '';
    document.getElementById('dmStatus').innerHTML = '';
  }

  return { open, close };
})();

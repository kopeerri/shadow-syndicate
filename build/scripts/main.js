/* =====================================================
   THE SHADOW SYNDICATE - Main JavaScript
   Core functionality and interactions
   ===================================================== */

// ========== MATRIX RAIN EFFECT ==========
class MatrixRain {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.characters = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF@#$%^&*';
    this.fontSize = 14;
    this.columns = 0;
    this.drops = [];

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this.columns = Math.floor(this.canvas.width / this.fontSize);
    this.drops = Array(this.columns).fill(1);
  }

  draw() {
    // Fade effect
    this.ctx.fillStyle = 'rgba(5, 5, 5, 0.05)';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Green text
    this.ctx.fillStyle = '#39FF14';
    this.ctx.font = `${this.fontSize}px monospace`;

    for (let i = 0; i < this.drops.length; i++) {
      const char = this.characters[Math.floor(Math.random() * this.characters.length)];
      const x = i * this.fontSize;
      const y = this.drops[i] * this.fontSize;

      // Varying opacity for depth
      this.ctx.globalAlpha = Math.random() * 0.5 + 0.1;
      this.ctx.fillText(char, x, y);
      this.ctx.globalAlpha = 1;

      // Reset drop randomly
      if (y > this.canvas.height && Math.random() > 0.975) {
        this.drops[i] = 0;
      }

      this.drops[i]++;
    }
  }

  start() {
    const animate = () => {
      this.draw();
      requestAnimationFrame(animate);
    };
    animate();
  }
}

// ========== WALLET CONNECTION MANAGER (Cardano) ==========
class WalletManager {
  constructor() {
    this.connected = false;
    this.walletName = null;
    this.balance = 0;
    this.address = '';
    this.api = null;

    this.init();
  }

  async init() {
    // Bind wallet modal globally — works on every page
    this._bindWalletModal();
    
    // Wait for wallet extension to inject window.cardano (CIP-30)
    // Extensions load asynchronously; poll for up to 2 seconds
    if (!window.cardano) {
      for (let i = 0; i < 20; i++) {
        await new Promise(r => setTimeout(r, 100));
        if (window.cardano) break;
      }
    }

    // Load saved state and reconnect silently
    const saved = localStorage.getItem('shadowSyndicate_wallet');
    if (saved) {
      const data = JSON.parse(saved);
      if (data.connected && data.walletName) {
        // Show reconnecting state
        const status = document.getElementById('connectionStatus');
        if (status) {
          status.className = 'status-indicator status-indicator--connected';
          status.innerHTML = '<span class="status-indicator__dot"></span><span>Syncing...</span>';
        }
        const ok = await this.connect(data.walletName, true);
        if (!ok) {
          localStorage.removeItem('shadowSyndicate_wallet');
          this.updateUI();
        }
      }
    }
  }

  async connect(walletName, silent = false) {
    // Debug: Log available wallets
    console.log('%c[WALLET] Checking for available wallets...', 'color: #00F0FF;');
    if (window.cardano) {
      const availableWallets = Object.keys(window.cardano).filter(k =>
        typeof window.cardano[k] === 'object' && window.cardano[k].enable
      );
      console.log('%c[WALLET] Available wallets:', 'color: #00F0FF;', availableWallets);
    } else {
      console.log('%c[WALLET] window.cardano not found - wallet extensions not detected', 'color: #FFA500;');
    }

    // Check if real wallet is available
    if (window.cardano && window.cardano[walletName]) {
      try {

        // PROMPT USER TO CONNECT
        this.api = await window.cardano[walletName].enable();

        this.connected = true;
        this.walletName = walletName;

        // Get real address from wallet
        this.address = await this.getWalletAddress();

        // Load balance for THIS address
        await this.loadBalanceForAddress();

        this.saveState();
        this.updateUI();

        // Notify components
        window.dispatchEvent(new CustomEvent('wallet:connected', { detail: { wallet: walletName, balance: this.balance, address: this.address } }));

        return true;

      } catch (err) {
        // Wallet API became stale (common after page refresh) — reset and retry once
        if (err.message && err.message.includes('shutdown')) {
          this.api = null;
          if (!silent) {
            // Retry once after a short delay
            await new Promise(r => setTimeout(r, 500));
            try {
              this.api = await window.cardano[walletName].enable();
              this.connected = true;
              this.walletName = walletName;
              this.address = await this.getWalletAddress();
              await this.loadBalanceForAddress();
              this.saveState();
              this.updateUI();
              window.dispatchEvent(new CustomEvent('wallet:connected', { detail: { wallet: walletName, balance: this.balance, address: this.address } }));
              return true;
            } catch (retryErr) {
              // Still failed — let user try manually
            }
          }
        }
        if (!silent) {
          // User rejected or wallet error — don't show raw error, just a clean message
          const msg = err.message && err.message.includes('refused') 
            ? 'Wallet connection was cancelled. Click Connect to try again.'
            : 'Wallet connection failed. Try refreshing the page.';
          alert(msg);
        }
        return false;
      }
    } else {
      // No wallet extension installed
      if (!silent) {
        alert('No Cardano wallet detected. Install Lace, Eternl, or Vespr to play with $SHADE.');
      }
      return false;
    }
  }

  // Simple hash for deterministic demo addresses
  hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
  }

  async loadBalanceForAddress() {
    // Always fetch from server
    if (typeof API !== 'undefined' && this.address) {
      try {
        API.setWallet(this.address);
        const session = await API.getSession();
        this.balance = session.balance || session.balance_units || 0;
        this.updateUI();
        window.dispatchEvent(new CustomEvent('wallet:balanceUpdated', { detail: { balance: this.balance } }));
        return;
      } catch (e) {
        console.log('[BALANCE] Server unreachable:', e.message);
      }
    }
    // Last resort fallback
    const storageKey = `shadowSyndicate_balance_${this.address}`;
    const storedBalance = localStorage.getItem(storageKey);
    this.balance = storedBalance ? parseFloat(storedBalance) : 0;
  }

  async refreshBalance() {
    if (!this.connected || !this.address) return;
    await this.loadBalanceForAddress();
  }

  async saveBalance() {
    const storageKey = `shadowSyndicate_balance_${this.address}`;
    localStorage.setItem(storageKey, this.balance.toString());
  }

  async getWalletAddress() {
    // Try to get bech32 address from CIP-30 API (preferred for Blockfrost)
    if (this.api) {
      try {
        // getChangeAddress returns bech32 (addr1...), preferred for Blockfrost queries
        const changeAddr = await this.api.getChangeAddress();
        if (changeAddr) {
          return changeAddr;
        }
      } catch (e) {
        console.warn('getChangeAddress failed, trying alternatives:', e.message);
      }
      try {
        const addresses = await this.api.getUsedAddresses();
        if (addresses && addresses.length > 0) {
          return addresses[0];
        }
        const rewardAddresses = await this.api.getRewardAddresses();
        if (rewardAddresses && rewardAddresses.length > 0) {
          return rewardAddresses[0];
        }
      } catch (err) {
        console.warn('Could not get wallet address:', err);
      }
    }
    // Fallback: generate deterministic address based on wallet name
    return `addr_${this.walletName}_${Date.now().toString(36)}`;
  }

  disconnect() {
    this.connected = false;
    this.walletName = null;
    this.balance = 0;
    this.address = '';
    this.api = null;

    localStorage.removeItem('shadowSyndicate_wallet');

    this.updateUI();
    window.dispatchEvent(new CustomEvent('wallet:disconnected'));
  }

  _bindWalletModal() {
    const self = this;
    // Open modal on connect button click
    const btn = document.getElementById('connectWalletBtn');
    if (btn && !btn._bound) {
      btn._bound = true;
      btn.addEventListener('click', () => {
        if (self.connected) {
          self.disconnect();
        } else {
          const modal = document.getElementById('walletModal');
          const backdrop = document.getElementById('walletModalBackdrop');
          if (modal) { modal.classList.add('active'); modal.style.display = ''; }
          if (backdrop) { backdrop.classList.add('active'); backdrop.style.display = ''; }
        }
      });
    }
    // Close modal
    const closeBtn = document.getElementById('closeWalletModal');
    if (closeBtn && !closeBtn._bound) {
      closeBtn._bound = true;
      closeBtn.addEventListener('click', () => self._closeWalletModal());
    }
    // Backdrop click to close
    const backdrop = document.getElementById('walletModalBackdrop');
    if (backdrop && !backdrop._bound) {
      backdrop._bound = true;
      backdrop.addEventListener('click', () => self._closeWalletModal());
    }
    // Wallet option clicks
    document.querySelectorAll('.wallet-option').forEach(opt => {
      if (opt._bound) return;
      opt._bound = true;
      opt.addEventListener('click', async () => {
        const name = opt.dataset.wallet;
        if (name && await self.connect(name)) {
          self._closeWalletModal();
        }
      });
    });
  }

  _closeWalletModal() {
    const modal = document.getElementById('walletModal');
    const backdrop = document.getElementById('walletModalBackdrop');
    if (modal) modal.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
  }

  saveState() {
    localStorage.setItem('shadowSyndicate_wallet', JSON.stringify({
      connected: this.connected,
      walletName: this.walletName,
      address: this.address
    }));
  }

  // Bech32 encoding for Cardano addresses
  BECH32_CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l';

  // Bech32 polymod for checksum
  bech32Polymod(values) {
    const GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3];
    let chk = 1;
    for (let v of values) {
      let top = chk >> 25;
      chk = ((chk & 0x1ffffff) << 5) ^ v;
      for (let i = 0; i < 5; i++) {
        if ((top >> i) & 1) chk ^= GEN[i];
      }
    }
    return chk;
  }

  // Expand HRP for checksum
  bech32HrpExpand(hrp) {
    let ret = [];
    for (let c of hrp) {
      ret.push(c.charCodeAt(0) >> 5);
    }
    ret.push(0);
    for (let c of hrp) {
      ret.push(c.charCodeAt(0) & 31);
    }
    return ret;
  }

  // Create bech32 checksum
  bech32CreateChecksum(hrp, data) {
    const values = this.bech32HrpExpand(hrp).concat(data).concat([0, 0, 0, 0, 0, 0]);
    const polymod = this.bech32Polymod(values) ^ 1;
    let ret = [];
    for (let i = 0; i < 6; i++) {
      ret.push((polymod >> (5 * (5 - i))) & 31);
    }
    return ret;
  }

  // Convert 8-bit bytes to 5-bit groups
  convertBits(data, fromBits, toBits, pad = true) {
    let acc = 0;
    let bits = 0;
    let ret = [];
    const maxv = (1 << toBits) - 1;

    for (let value of data) {
      acc = (acc << fromBits) | value;
      bits += fromBits;
      while (bits >= toBits) {
        bits -= toBits;
        ret.push((acc >> bits) & maxv);
      }
    }

    if (pad && bits > 0) {
      ret.push((acc << (toBits - bits)) & maxv);
    }

    return ret;
  }

  // Convert hex address to bech32
  hexToBech32(hexAddr) {
    if (!hexAddr || hexAddr.startsWith('addr')) return hexAddr;

    try {
      // Determine HRP based on first byte (network tag)
      const firstByte = parseInt(hexAddr.substring(0, 2), 16);
      const networkId = firstByte & 0x0f;
      const hrp = networkId === 1 ? 'addr' : 'addr_test';

      // Convert hex to bytes
      const bytes = [];
      for (let i = 0; i < hexAddr.length; i += 2) {
        bytes.push(parseInt(hexAddr.substring(i, i + 2), 16));
      }

      // Convert to 5-bit groups
      const data = this.convertBits(bytes, 8, 5);

      // Create checksum
      const checksum = this.bech32CreateChecksum(hrp, data);

      // Encode
      let result = hrp + '1';
      for (let d of data.concat(checksum)) {
        result += this.BECH32_CHARSET[d];
      }

      return result;
    } catch (e) {
      console.warn('Bech32 conversion failed:', e);
      return hexAddr;
    }
  }

  shortenAddress(addr) {
    if (!addr || addr.length < 20) return addr;

    // Convert hex to bech32 if needed
    let displayAddr = addr;
    if (!addr.startsWith('addr') && /^[0-9a-fA-F]+$/.test(addr)) {
      displayAddr = this.hexToBech32(addr);
    }

    return displayAddr.substring(0, 12) + '...' + displayAddr.substring(displayAddr.length - 8);
  }

  updateUI() {
    const statusIndicator = document.getElementById('connectionStatus');
    const connectBtn = document.getElementById('connectWalletBtn');
    const balanceDisplays = document.querySelectorAll('[data-balance], #balanceDisplay');

    if (statusIndicator) {
      if (this.connected) {
        statusIndicator.className = 'status-indicator status-indicator--connected';
        statusIndicator.innerHTML = `
          <span class="status-indicator__dot"></span>
          <span>${this.walletName?.toUpperCase() || 'CONN'}</span>
        `;
      } else {
        statusIndicator.className = 'status-indicator status-indicator--disconnected';
        statusIndicator.innerHTML = `
          <span class="status-indicator__dot"></span>
          <span>Offline</span>
        `;
      }
    }

    if (connectBtn) {
      if (this.connected) {
        connectBtn.textContent = 'DISCONNECT';
        connectBtn.classList.remove('btn-cyan');
        connectBtn.classList.add('btn-secondary');
      } else {
        connectBtn.innerHTML = '<span>⬡</span> CONNECT WALLET';
        connectBtn.classList.add('btn-cyan');
        connectBtn.classList.remove('btn-secondary');
      }
    }

    // Update balances
    balanceDisplays.forEach(el => {
      const formatted = this.connected ?
        this.balance.toLocaleString() + ' $SHADE'
        : '---';
      el.textContent = formatted;
    });

    // Update header balance on index page
    const headerBal = document.getElementById('headerBalance');
    if (headerBal) {
      if (this.connected) {
        headerBal.textContent = this.balance.toLocaleString() + ' $SHADE';
        headerBal.style.display = 'inline';
      } else {
        headerBal.style.display = 'none';
      }
    }
  }

  getBalance() {
    return this.connected ? this.balance : 0;
  }

  async updateBalance(delta) {
    if (!this.connected || !this.address) return;
    this.balance += delta;
    this.updateUI();
    const addr = this.address;
    fetch(`${API.baseURL}/balance/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ wallet_address: addr, delta: delta }),
      keepalive: true,
    }).catch(e => {});
    window.dispatchEvent(new CustomEvent('wallet:balanceUpdated', { detail: { balance: this.balance } }));
  }
}

// ========== MODAL MANAGER ==========
class ModalManager {
  constructor() {
    this.activeModal = null;
    this.init();
  }

  init() {
    // Close on backdrop click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', () => this.close());
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.activeModal) {
        this.close();
      }
    });
  }

  open(modalId) {
    const modal = document.getElementById(modalId);
    const backdrop = document.getElementById(modalId + 'Backdrop') ||
      document.getElementById('walletModalBackdrop');

    if (modal && backdrop) {
      backdrop.classList.add('active');
      modal.classList.add('active');
      this.activeModal = modal;
      document.body.style.overflow = 'hidden';
    }
  }

  close() {
    if (this.activeModal) {
      const backdrop = document.querySelector('.modal-backdrop.active');
      if (backdrop) backdrop.classList.remove('active');
      this.activeModal.classList.remove('active');
      this.activeModal = null;
      document.body.style.overflow = '';
    }
  }
}

// ========== GLITCH TEXT EFFECT ==========
class GlitchText {
  constructor(element) {
    this.element = element;
    this.originalText = element.textContent;
    this.glitchChars = '!@#$%^&*()_+-=[]{}|;:,.<>?/~`';
    this.isGlitching = false;
  }

  glitch(duration = 100) {
    if (this.isGlitching) return;
    this.isGlitching = true;

    const originalText = this.originalText;
    let iterations = 0;
    const maxIterations = 10;

    const interval = setInterval(() => {
      this.element.textContent = originalText
        .split('')
        .map((char, index) => {
          if (index < iterations) return originalText[index];
          return this.glitchChars[Math.floor(Math.random() * this.glitchChars.length)];
        })
        .join('');

      iterations++;

      if (iterations > maxIterations) {
        clearInterval(interval);
        this.element.textContent = originalText;
        this.isGlitching = false;
      }
    }, duration / maxIterations);
  }
}

// ========== NUMBER SCRAMBLE EFFECT ==========
function scrambleNumber(element, targetValue, duration = 1000) {
  const startTime = Date.now();
  const startValue = parseInt(element.textContent) || 0;

  const animate = () => {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Easing
    const easeOut = 1 - Math.pow(1 - progress, 3);

    // During animation, show random numbers
    if (progress < 1) {
      const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOut);
      element.textContent = currentValue.toLocaleString();
      requestAnimationFrame(animate);
    } else {
      element.textContent = targetValue.toLocaleString();
    }
  };

  animate();
}

// ========== TERMINAL LOG ==========
class TerminalLog {
  constructor(container, maxLines = 50) {
    this.container = container;
    this.maxLines = maxLines;
    this.lines = [];
  }

  log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    const prefix = {
      info: '[INFO]',
      success: '[OK]',
      error: '[ERR]',
      warning: '[WARN]'
    }[type] || '[LOG]';

    const line = document.createElement('div');
    line.className = 'terminal-log__line';
    line.innerHTML = `
      <span class="terminal-log__timestamp">${timestamp}</span>
      <span class="terminal-log__prefix">${prefix}</span>
      <span class="terminal-log__message terminal-log__message--${type}">${message}</span>
    `;

    this.container.appendChild(line);
    this.lines.push(line);

    // Remove old lines
    while (this.lines.length > this.maxLines) {
      const oldLine = this.lines.shift();
      oldLine.remove();
    }

    // Scroll to bottom
    this.container.scrollTop = this.container.scrollHeight;
  }

  clear() {
    this.container.innerHTML = '';
    this.lines = [];
  }
}

// ========== PROOF GENERATION OVERLAY ==========
class ProofGenerator {
  constructor() {
    this.overlay = null;
    this.createOverlay();
  }

  createOverlay() {
    this.overlay = document.createElement('div');
    this.overlay.className = 'loading-overlay';
    this.overlay.style.display = 'none';
    this.overlay.innerHTML = `
      <div class="terminal-frame" style="max-width: 400px; text-align: center;">
        <h4 style="color: var(--cyber-cyan); margin-bottom: var(--space-4);">GENERATING ZK PROOF</h4>
        <div class="loading-spinner" style="margin: 0 auto var(--space-4);"></div>
        <div class="terminal-log" id="proofLog" style="text-align: left; font-size: var(--text-xs); max-height: 150px;"></div>
        <p class="loading-text loading-dots" style="margin-top: var(--space-4);">Decrypting</p>
      </div>
    `;
    document.body.appendChild(this.overlay);
  }

  async show(duration = 2000) {
    this.overlay.style.display = 'flex';
    const log = this.overlay.querySelector('#proofLog');
    log.innerHTML = '';

    const messages = [
      { text: 'Initializing ZK circuit...', delay: 100 },
      { text: 'Loading witness data...', delay: 300 },
      { text: 'Computing polynomial commitment...', delay: 600 },
      { text: 'Generating proof transcript...', delay: 1000 },
      { text: 'Verifying constraints...', delay: 1400 },
      { text: 'Proof generation complete.', delay: duration - 200, type: 'success' }
    ];

    for (const msg of messages) {
      await new Promise(resolve => setTimeout(resolve, msg.delay - (messages.indexOf(msg) > 0 ? messages[messages.indexOf(msg) - 1].delay : 0)));
      const line = document.createElement('div');
      line.style.color = msg.type === 'success' ? 'var(--phosphor-green)' : 'var(--text-secondary)';
      line.textContent = `> ${msg.text}`;
      log.appendChild(line);
      log.scrollTop = log.scrollHeight;
    }

    await new Promise(resolve => setTimeout(resolve, 300));
  }

  hide() {
    this.overlay.style.display = 'none';
  }
}

// ========== SMOOTH SCROLL ==========
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        const headerOffset = 100;
        const elementPosition = target.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

// ========== INTERSECTION OBSERVER FOR ANIMATIONS ==========
// ========== INTERSECTION OBSERVER FOR ANIMATIONS ==========
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1'; // Fix: Ensure opacity is reset to 1
        entry.target.style.animationPlayState = 'running';
        entry.target.classList.add('visible');
        observer.unobserve(entry.target); // Stop observing once triggered
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });

  document.querySelectorAll('.fade-in-up, .fade-in, .fade-in-scale').forEach(el => {
    el.style.opacity = '0';
    el.style.animationPlayState = 'paused';
    observer.observe(el);
  });
}

// ========== GLOBAL INSTANCES ==========
let walletManager;
let modalManager;
let proofGenerator;
let matrixRain;

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
  // Initialize Matrix Rain on hero canvas
  const matrixCanvas = document.getElementById('matrixCanvas');
  if (matrixCanvas) {
    matrixRain = new MatrixRain(matrixCanvas);
    matrixRain.start();
  }

  // ========== SMART HEADER ==========
  let lastScroll = 0;
  const header = document.querySelector('.header');

  if (header) {
    window.addEventListener('scroll', () => {
      const currentScroll = window.pageYOffset;

      if (currentScroll <= 0) {
        header.classList.remove('header--hidden');
        return;
      }

      if (currentScroll > lastScroll && !header.classList.contains('header--hidden')) {
        // Scrolling down
        header.classList.add('header--hidden');
      } else if (currentScroll < lastScroll && header.classList.contains('header--hidden')) {
        // Scrolling up
        header.classList.remove('header--hidden');
      }

      lastScroll = currentScroll;
    });

    // Show header on mouse hover at top
    document.addEventListener('mousemove', (e) => {
      if (e.clientY < 100 && header.classList.contains('header--hidden')) {
        header.classList.remove('header--hidden');
      }
    });
  }

  // ========== COLLAPSIBLE GAME HEADER ==========
  const gameHeader = document.getElementById('gameHeader');
  const headerToggle = document.getElementById('headerToggle');

  if (gameHeader && headerToggle) {
    // Restore saved state
    const isCollapsed = localStorage.getItem('shadowSyndicate_headerCollapsed') === 'true';
    if (isCollapsed) {
      gameHeader.classList.add('collapsed');
    }

    headerToggle.addEventListener('click', () => {
      gameHeader.classList.toggle('collapsed');
      const nowCollapsed = gameHeader.classList.contains('collapsed');
      localStorage.setItem('shadowSyndicate_headerCollapsed', nowCollapsed.toString());
    });
  }

  // Initialize managers
  walletManager = new WalletManager();
  modalManager = new ModalManager();
  proofGenerator = new ProofGenerator();

  // Wallet connection buttons
  const connectBtns = document.querySelectorAll('#connectWalletBtn, #ctaConnectBtn');
  connectBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (walletManager.connected) {
        walletManager.disconnect();
      } else {
        modalManager.open('walletModal');
      }
    });
  });

  // Close wallet modal
  const closeModalBtn = document.getElementById('closeWalletModal');
  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => modalManager.close());
  }

  // Wallet options
  document.querySelectorAll('.wallet-option').forEach(option => {
    option.addEventListener('click', async () => {
      const walletType = option.dataset.wallet;
      option.style.opacity = '0.5';
      option.style.pointerEvents = 'none';

      await walletManager.connect(walletType);
      modalManager.close();

      option.style.opacity = '1';
      option.style.pointerEvents = 'auto';
    });
  });

  // Initialize smooth scroll
  initSmoothScroll();

  // Initialize scroll animations
  initScrollAnimations();

  // Glitch effect on hover for title
  const glitchElements = document.querySelectorAll('.glitch');
  glitchElements.forEach(el => {
    const glitch = new GlitchText(el);
    el.addEventListener('mouseenter', () => glitch.glitch(200));
  });

  console.log('%c[SHADOW SYNDICATE] Node Zero initialized.', 'color: #39FF14; font-family: monospace;');
  console.log('%c"What happens in the dark, stays in the dark."', 'color: #00F0FF; font-style: italic;');
});

// Export for use in game modules
window.ShadowSyndicate = {
  wallet: () => walletManager,
  modal: () => modalManager,
  proof: () => proofGenerator,
  TerminalLog,
  // Shared game stats — call from any page, dashboard reads from localStorage
  recordGameResult: (game, betAmount, won, payout) => {
    const profit = won ? (payout - betAmount) : -betAmount;
    const saved = localStorage.getItem('shadowSyndicate_stats');
    const stats = saved ? JSON.parse(saved) : { totalWagers: 0, totalProfit: 0, biggestWin: 0 };
    stats.totalWagers++;
    stats.totalProfit += profit;
    if (won && profit > stats.biggestWin) stats.biggestWin = profit;
    localStorage.setItem('shadowSyndicate_stats', JSON.stringify(stats));
    return stats;
  }
};

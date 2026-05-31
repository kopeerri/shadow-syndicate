/* =====================================================
   SHADOW SYNDICATE - Scroll Animations
   IntersectionObserver-based reveal animations
   ===================================================== */

class ScrollAnimations {
    constructor() {
        this.observerOptions = {
            root: null,
            rootMargin: '0px 0px -50px 0px',
            threshold: 0.1
        };
        this.init();
    }

    init() {
        // Create observer for fade-in elements
        this.fadeObserver = new IntersectionObserver(
            (entries) => this.handleFadeIn(entries),
            this.observerOptions
        );

        // Create observer for stagger animations
        this.staggerObserver = new IntersectionObserver(
            (entries) => this.handleStagger(entries),
            { ...this.observerOptions, threshold: 0.05 }
        );

        // Observe elements after DOM is ready
        this.observeElements();
    }

    observeElements() {
        // Fade-in elements
        document.querySelectorAll('[data-animate="fade-up"]').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            this.fadeObserver.observe(el);
        });

        document.querySelectorAll('[data-animate="fade-scale"]').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'scale(0.95)';
            this.fadeObserver.observe(el);
        });

        // Stagger containers (will animate children)
        document.querySelectorAll('[data-animate-stagger]').forEach(container => {
            this.staggerObserver.observe(container);
        });
    }

    handleFadeIn(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const delay = el.dataset.animateDelay || 0;

                setTimeout(() => {
                    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0) scale(1)';
                }, delay);

                this.fadeObserver.unobserve(el);
            }
        });
    }

    handleStagger(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const children = container.querySelectorAll('[data-animate-child]');

                children.forEach((child, index) => {
                    child.style.opacity = '0';
                    child.style.transform = 'translateY(20px)';

                    setTimeout(() => {
                        child.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                        child.style.opacity = '1';
                        child.style.transform = 'translateY(0)';
                    }, index * 100); // 100ms stagger between each
                });

                this.staggerObserver.unobserve(container);
            }
        });
    }
}

/* =====================================================
   Number Count-Up Animation
   Animates numbers from 0 when entering viewport
   ===================================================== */
class CountUpAnimation {
    constructor() {
        this.observer = new IntersectionObserver(
            (entries) => this.handleCountUp(entries),
            { threshold: 0.3 }
        );
        this.observeElements();
    }

    observeElements() {
        document.querySelectorAll('[data-count-up]').forEach(el => {
            const text = el.textContent.replace(/[,+\-]/g, '');
            const target = parseFloat(text) || 0;
            el.dataset.countTarget = target;
            el.dataset.countPrefix = el.textContent.startsWith('+') ? '+' :
                el.textContent.startsWith('-') ? '-' : '';
            el.textContent = el.dataset.countPrefix + '0';
            this.observer.observe(el);
        });
    }

    handleCountUp(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseFloat(el.dataset.countTarget);
                const prefix = el.dataset.countPrefix || '';
                const duration = 1500;
                const startTime = performance.now();

                const animate = (currentTime) => {
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = Math.floor(target * eased);

                    el.textContent = prefix + current.toLocaleString();

                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        el.textContent = prefix + target.toLocaleString();
                    }
                };

                requestAnimationFrame(animate);
                this.observer.unobserve(el);
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.scrollAnimations = new ScrollAnimations();
    window.countUpAnimation = new CountUpAnimation();

    // Button ripple effect
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn');
        if (!btn) return;

        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;

        btn.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
});

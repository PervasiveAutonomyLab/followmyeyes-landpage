document.addEventListener('DOMContentLoaded', () => {
  // only play the looping clips that are on screen
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) e.target.play().catch(() => {});
        else e.target.pause();
      }
    }, { threshold: 0.15 });
    document.querySelectorAll('video[autoplay]').forEach((v) => observer.observe(v));
  }

  document.querySelectorAll('.copy-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const code = document.getElementById(btn.dataset.target);
      if (!code || !navigator.clipboard) return;
      navigator.clipboard.writeText(code.innerText).then(() => {
        const label = btn.querySelector('span:last-child');
        label.textContent = 'Copied';
        setTimeout(() => { label.textContent = 'Copy'; }, 1500);
      });
    });
  });
});

// simple tab switcher for the qualitative examples
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tabs-lite').forEach((bar) => {
    const group = bar.dataset.group;
    bar.querySelectorAll('button').forEach((b) => {
      b.addEventListener('click', () => {
        bar.querySelectorAll('button').forEach((x) => x.classList.toggle('active', x === b));
        document.querySelectorAll(`.tab-panel[data-group="${group}"]`).forEach((p) =>
          p.classList.toggle('active', p.dataset.tab === b.dataset.tab));
      });
    });
  });
});

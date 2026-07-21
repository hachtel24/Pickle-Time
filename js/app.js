document.addEventListener('DOMContentLoaded', () => {

  // --- Mobile Hamburger Menu ---
  const menuToggle = document.getElementById('menuToggle');
  const navMenu = document.getElementById('navMenu');

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
      menuToggle.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        menuToggle.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }

  // --- Menu Category Filtering ---
  const tabBtns = document.querySelectorAll('.tab-btn');
  const menuEntries = document.querySelectorAll('#menuGrid [data-category]');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const category = btn.getAttribute('data-category');

      menuEntries.forEach(entry => {
        const entryCategory = entry.getAttribute('data-category');
        if (category === 'all' || entryCategory === category) {
          entry.style.display = '';
          entry.style.opacity = '0';
          setTimeout(() => {
            entry.style.opacity = '1';
            entry.style.transition = 'opacity 0.35s ease';
          }, 20);
        } else {
          entry.style.display = 'none';
        }
      });
    });
  });

  // --- Real Store Hours: Open/Closed Status ---
  // 0 = Sunday ... 6 = Saturday. Closed Sundays, otherwise 10:30am-8:30pm.
  const STORE_HOURS = {
    0: null,
    1: [10.5, 20.5],
    2: [10.5, 20.5],
    3: [10.5, 20.5],
    4: [10.5, 20.5],
    5: [10.5, 20.5],
    6: [10.5, 20.5],
  };
  const DAY_LABELS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  function formatHours(range) {
    if (!range) return 'Closed';
    const fmt = (h) => {
      const hour24 = Math.floor(h);
      const minutes = Math.round((h - hour24) * 60);
      const period = hour24 >= 12 ? 'PM' : 'AM';
      let hour12 = hour24 % 12;
      if (hour12 === 0) hour12 = 12;
      return minutes ? `${hour12}:${minutes.toString().padStart(2, '0')} ${period}` : `${hour12} ${period}`;
    };
    return `${fmt(range[0])} - ${fmt(range[1])}`;
  }

  function updateStoreStatus() {
    const now = new Date();
    const day = now.getDay();
    const timeDecimal = now.getHours() + now.getMinutes() / 60;
    const range = STORE_HOURS[day];
    const isOpen = !!range && timeDecimal >= range[0] && timeDecimal < range[1];

    let closedMessage = 'Closed';
    if (!isOpen) {
      if (range && timeDecimal < range[0]) {
        closedMessage = `Closed — opens today at ${formatHours(range).split(' - ')[0]}`;
      } else {
        let nextDay = (day + 1) % 7;
        while (!STORE_HOURS[nextDay]) nextDay = (nextDay + 1) % 7;
        closedMessage = `Closed — opens ${DAY_LABELS[nextDay]} at ${formatHours(STORE_HOURS[nextDay]).split(' - ')[0]}`;
      }
    }

    document.querySelectorAll('[data-ticker-status]').forEach(el => {
      el.textContent = isOpen ? 'Open Now' : closedMessage;
    });
    document.querySelectorAll('[data-ticker-dot]').forEach(el => {
      el.classList.toggle('closed', !isOpen);
    });

    const locationStatusValue = document.getElementById('locationStatusValue');
    if (locationStatusValue) {
      locationStatusValue.textContent = isOpen ? 'Open Now' : 'Closed Now';
    }

    const todayHours = document.getElementById('todayHours');
    if (todayHours) {
      todayHours.textContent = `${DAY_LABELS[day]}: ${formatHours(range)}`;
    }

    document.querySelectorAll('#hoursTable tr').forEach(row => {
      const rowDay = Number(row.getAttribute('data-day'));
      row.classList.toggle('today', rowDay === day);
    });
  }

  updateStoreStatus();
  setInterval(updateStoreStatus, 60000);

  // --- Footer Year ---
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // --- Scroll Racer: mascot travels down the rail as the page scrolls ---
  const racerRail = document.querySelector('.scroll-racer');
  const racerMascot = document.getElementById('scrollRacerMascot');

  function updateScrollRacer() {
    if (!racerRail || !racerMascot) return;
    const trackHeight = racerRail.clientHeight - racerMascot.clientHeight;
    const doc = document.documentElement;
    const scrollableHeight = doc.scrollHeight - doc.clientHeight;
    const percent = scrollableHeight > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollableHeight)) : 0;
    racerMascot.style.top = `${percent * trackHeight}px`;
  }

  if (racerRail && racerMascot) {
    window.addEventListener('scroll', updateScrollRacer, { passive: true });
    window.addEventListener('resize', updateScrollRacer);
    updateScrollRacer();
  }
});

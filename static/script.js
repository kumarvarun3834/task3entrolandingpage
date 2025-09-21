/* Mobile nav toggle */
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');

navToggle?.addEventListener('click', () => {
  navMenu.classList.toggle('open');
  if (navMenu.classList.contains('open')) {
    navMenu.style.display = 'flex';
    navToggle.setAttribute('aria-expanded', 'true');
  } else {
    navMenu.style.display = '';
    navToggle.setAttribute('aria-expanded', 'false');
  }
});

document.querySelectorAll('.nav-menu a').forEach(link => {
  link.addEventListener('click', () => {
    navMenu.classList.remove('open');
    navMenu.style.display = '';
    navToggle.setAttribute('aria-expanded', 'false');
  });
});

document.addEventListener('click', (e) => {
  if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
    navMenu.classList.remove('open');
    navMenu.style.display = '';
    navToggle.setAttribute('aria-expanded', 'false');
  }
});

/* Set year */
document.getElementById('year').textContent = new Date().getFullYear();

/* Smooth scrolling */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

/* Scroll reveal */
const revealElems = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
revealElems.forEach(el => revealObserver.observe(el));

/* Contact form validation */
const contactForm = document.getElementById('contactForm');
const formStatus = document.getElementById('formStatus');
const submitBtn = document.getElementById('submitBtn');

if (contactForm) {
  const inputs = contactForm.querySelectorAll('input, textarea');

  inputs.forEach(input => {
    input.addEventListener('blur', () => validateField(input));
    input.addEventListener('input', () => clearFieldError(input));
  });

  function validateField(field) {
    const value = field.value.trim();
    if (field.hasAttribute('required') && !value) {
      field.style.borderColor = '#EF4444';
      return false;
    }
    if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      field.style.borderColor = '#EF4444';
      return false;
    }
    field.style.borderColor = '#10B981';
    return true;
  }
  function clearFieldError(field) {
    if (field.style.borderColor === '#EF4444') field.style.borderColor = '';
  }

  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    formStatus.textContent = '';

    let isValid = true;
    inputs.forEach(input => { if (!validateField(input)) isValid = false; });
    if (!isValid) {
      formStatus.style.color = 'crimson';
      formStatus.textContent = 'Please fill all fields correctly';
      return;
    }

    const origText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite;">⟳</span> Sending...';

    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      formStatus.style.color = 'green';
      formStatus.textContent = 'Message sent successfully!';
      contactForm.reset();
      inputs.forEach(input => input.style.borderColor = '');
    } catch {
      formStatus.style.color = 'crimson';
      formStatus.textContent = 'Server error. Try again later.';
    } finally {
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = origText;
      }, 1000);
    }
  });
}

/* Enhanced service card interactions */
document.querySelectorAll('.service').forEach(card => {
  card.addEventListener('mouseenter', function() {
    this.style.transform = 'translateY(-8px) scale(1.02)';
  });
  card.addEventListener('mouseleave', function() {
    this.style.transform = '';
  });
  card.addEventListener('click', function() {
    this.style.transform = 'translateY(-4px) scale(0.98)';
    setTimeout(() => { this.style.transform = ''; }, 150);
  });
});

/* Service request form logic */
const s_service = document.getElementById('s_service');
const subDetailsContainer = document.getElementById('subDetailsContainer');
const s_sub_details = document.getElementById('s_sub_details');
const serviceForm = document.getElementById('serviceForm');
const serviceMessage = document.getElementById('serviceMessage');

if (s_service) {
  s_service.addEventListener('change', () => {
    if (s_service.value === 'Web Development' || s_service.value === 'Application Development') {
      subDetailsContainer.style.display = 'block';
      s_sub_details.required = true;
    } else {
      subDetailsContainer.style.display = 'none';
      s_sub_details.required = false;
      s_sub_details.value = '';
    }
  });

  serviceForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    serviceMessage.style.display = 'none';

    const data = {
      name: document.getElementById('s_name').value.trim(),
      email: document.getElementById('s_email').value.trim(),
      phone: document.getElementById('s_phone').value.trim(),
      service: s_service.value,
      sub_details: s_sub_details.value.trim(),
      details: document.getElementById('s_details').value.trim(),
      notes: document.getElementById('s_notes').value.trim(),
      platform: document.getElementById('s_platform').value.trim(),
      attachment_link: document.getElementById('s_attachment_link').value.trim(),
      priority: document.getElementById('s_priority').value,
      budget: document.getElementById('s_budget').value,
      deadline: document.getElementById('s_deadline').value,
    };

    try {
      // Demo only: simulate server
      await new Promise(resolve => setTimeout(resolve, 1500));
      serviceMessage.style.display = 'block';
      serviceMessage.className = 'message success';
      serviceMessage.innerText = '✅ Service request submitted!';
      serviceForm.reset();
      subDetailsContainer.style.display = 'none';
    } catch {
      serviceMessage.style.display = 'block';
      serviceMessage.className = 'message error';
      serviceMessage.innerText = '⚠ Could not connect to server.';
    }
  });
}

/* Spinner animation */
const style = document.createElement('style');
style.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`;
document.head.appendChild(style);

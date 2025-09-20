/* Mobile nav toggle - Enhanced with better UX */
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

// Close menu when clicking nav links
document.querySelectorAll('.nav-menu a').forEach(link => {
  link.addEventListener('click', () => {
    navMenu.classList.remove('open');
    navMenu.style.display = '';
    navToggle.setAttribute('aria-expanded', 'false');
  });
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
  if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
    navMenu.classList.remove('open');
    navMenu.style.display = '';
    navToggle.setAttribute('aria-expanded', 'false');
  }
});

/* Set year */
document.getElementById('year').textContent = new Date().getFullYear();

/* Enhanced smooth scrolling for anchor links */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

/* Scroll reveal: add 'active' to .reveal when section enters view - Enhanced */
const revealElems = document.querySelectorAll('.reveal');
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('active');
      revealObserver.unobserve(entry.target); // one-time reveal
    }
  });
}, { 
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
});

revealElems.forEach(el => revealObserver.observe(el));

/* Contact form: Enhanced validation, spinner & better UX */
const contactForm = document.getElementById('contactForm');
const formStatus = document.getElementById('formStatus');
const submitBtn = document.getElementById('submitBtn');

if (contactForm) {
  // Enhanced real-time validation
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
    
    if (field.type === 'email' && value && !isValidEmail(value)) {
      field.style.borderColor = '#EF4444';
      return false;
    }
    
    field.style.borderColor = '#10B981';
    return true;
  }
  
  function clearFieldError(field) {
    if (field.style.borderColor === '#EF4444' || field.style.borderColor === 'rgb(239, 68, 68)') {
      field.style.borderColor = '';
    }
  }
  
  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    formStatus.textContent = '';
    
    const name = contactForm.name.value.trim();
    const email = contactForm.email.value.trim();
    const message = contactForm.message.value.trim();

    // Enhanced validation
    let isValid = true;
    inputs.forEach(input => {
      if (!validateField(input)) {
        isValid = false;
      }
    });

    if (!isValid) {
      formStatus.style.color = 'crimson';
      formStatus.textContent = 'Please fill all fields correctly';
      return;
    }

    // Enhanced loading state
    const origText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite;">⟳</span> Sending...';

    try {
      // Simulate successful submission for demo
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      formStatus.style.color = 'green';
      formStatus.textContent = 'Message sent successfully! We\'ll get back to you soon.';
      contactForm.reset();
      
      // Reset field borders
      inputs.forEach(input => input.style.borderColor = '');
      
    } catch (err) {
      formStatus.style.color = 'crimson';
      formStatus.textContent = 'Server error. Please try again later or email us directly.';
    } finally {
      // Reset button with delay for better UX
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
  
  // Add click effect
  card.addEventListener('click', function() {
    this.style.transform = 'translateY(-4px) scale(0.98)';
    setTimeout(() => {
      this.style.transform = '';
    }, 150);
  });
});

/* Add loading animation styles */
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);
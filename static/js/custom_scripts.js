// static/js/custom_scripts.js
// DENSO Project Manager Pro - Custom JavaScript

/**
 * Custom JavaScript for enhanced user experience
 * Handles animations, interactions, and UI enhancements
 */

(function () {
  'use strict';

  // ===========================================
  // GLOBAL VARIABLES
  // ===========================================

  let isInitialized = false;
  let notificationQueue = [];
  let performanceMetrics = {
    pageLoadTime: 0,
    interactionCount: 0,
    errors: [],
  };

  // ===========================================
  // INITIALIZATION
  // ===========================================

  function initializeApp() {
    if (isInitialized) return;

    console.log('🚀 Initializing DENSO Project Manager Pro');

    // Track page load time
    trackPageLoadTime();

    // Setup event listeners
    setupEventListeners();

    // Initialize components
    initializeComponents();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    // Initialize tooltips
    initializeTooltips();

    // Setup theme management
    initializeThemeManager();

    // Setup notification system
    initializeNotifications();

    // Setup performance monitoring
    initializePerformanceMonitoring();

    isInitialized = true;
    console.log('✅ DENSO Project Manager Pro initialized successfully');
  }

  // ===========================================
  // PERFORMANCE TRACKING
  // ===========================================

  function trackPageLoadTime() {
    const startTime = performance.now();

    window.addEventListener('load', function () {
      const loadTime = performance.now() - startTime;
      performanceMetrics.pageLoadTime = loadTime;

      console.log(`📊 Page load time: ${loadTime.toFixed(2)}ms`);

      // Send to analytics if needed
      if (window.gtag) {
        gtag('event', 'page_load_time', {
          value: Math.round(loadTime),
          custom_parameter: 'denso_pm',
        });
      }
    });
  }

  function initializePerformanceMonitoring() {
    // Monitor interactions
    document.addEventListener('click', function () {
      performanceMetrics.interactionCount++;
    });

    // Monitor errors
    window.addEventListener('error', function (event) {
      performanceMetrics.errors.push({
        message: event.message,
        source: event.filename,
        line: event.lineno,
        timestamp: new Date().toISOString(),
      });

      console.error('🔴 JavaScript Error:', event.message);
    });

    // Report performance metrics every 30 seconds
    setInterval(reportPerformanceMetrics, 30000);
  }

  function reportPerformanceMetrics() {
    const metrics = {
      ...performanceMetrics,
      memoryUsage: performance.memory
        ? {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576), // MB
            total: Math.round(performance.memory.totalJSHeapSize / 1048576), // MB
          }
        : null,
      connectionType: navigator.connection ? navigator.connection.effectiveType : 'unknown',
    };

    console.log('📈 Performance Metrics:', metrics);

    // Reset interaction count
    performanceMetrics.interactionCount = 0;
  }

  // ===========================================
  // EVENT LISTENERS
  // ===========================================

  function setupEventListeners() {
    // Smooth scrolling for anchor links
    document.addEventListener('click', function (e) {
      if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const target = document.querySelector(e.target.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
          });
        }
      }
    });

    // Enhanced button interactions
    document.addEventListener('click', function (e) {
      if (e.target.matches('.btn, .glass-button')) {
        createRippleEffect(e);
      }
    });

    // Auto-save form data
    document.addEventListener('input', function (e) {
      if (e.target.matches('input, textarea, select')) {
        debounce(autoSaveFormData, 1000)(e.target);
      }
    });

    // Handle file uploads with progress
    document.addEventListener('change', function (e) {
      if (e.target.type === 'file') {
        handleFileUpload(e.target);
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', function (e) {
      handleKeyboardNavigation(e);
    });
  }

  // ===========================================
  // UI ENHANCEMENTS
  // ===========================================

  function createRippleEffect(e) {
    const button = e.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');

    // Add ripple styles
    const style = document.createElement('style');
    if (!document.querySelector('#ripple-styles')) {
      style.id = 'ripple-styles';
      style.textContent = `
                .ripple {
                    position: absolute;
                    border-radius: 50%;
                    background: rgba(255, 255, 255, 0.6);
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                    pointer-events: none;
                }
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
      document.head.appendChild(style);
    }

    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  function initializeComponents() {
    // Animate cards on scroll
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px',
      }
    );

    // Observe all cards
    document.querySelectorAll('.glass-card, .metric-card, .task-card').forEach((card) => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      observer.observe(card);
    });

    // Initialize progress bars animation
    animateProgressBars();

    // Initialize counters animation
    animateCounters();
  }

  function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach((bar) => {
      const width = bar.style.width || bar.getAttribute('data-width') || '0%';
      bar.style.width = '0%';

      setTimeout(() => {
        bar.style.transition = 'width 1s ease-in-out';
        bar.style.width = width;
      }, 100);
    });
  }

  function animateCounters() {
    const counters = document.querySelectorAll('[data-count]');
    counters.forEach((counter) => {
      const target = parseInt(counter.getAttribute('data-count'));
      const duration = 2000; // 2 seconds
      const increment = target / (duration / 16); // 60fps
      let current = 0;

      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        counter.textContent = Math.floor(current).toLocaleString();
      }, 16);
    });
  }

  // ===========================================
  // KEYBOARD SHORTCUTS
  // ===========================================

  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
      // Ctrl/Cmd + K for search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openSearchModal();
      }

      // Ctrl/Cmd + N for new project
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        triggerNewProject();
      }

      // Ctrl/Cmd + Shift + T for new task
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        triggerNewTask();
      }

      // Esc to close modals
      if (e.key === 'Escape') {
        closeAllModals();
      }
    });
  }

  function handleKeyboardNavigation(e) {
    // Tab navigation enhancement
    if (e.key === 'Tab') {
      const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  }

  // ===========================================
  // TOOLTIP SYSTEM
  // ===========================================

  function initializeTooltips() {
    let tooltip = null;

    document.addEventListener(
      'mouseenter',
      function (e) {
        const element = e.target.closest('[data-tooltip]');
        if (!element) return;

        const text = element.getAttribute('data-tooltip');
        const position = element.getAttribute('data-tooltip-position') || 'top';

        tooltip = createTooltip(text, position);
        positionTooltip(tooltip, element, position);
        document.body.appendChild(tooltip);

        // Animate in
        requestAnimationFrame(() => {
          tooltip.style.opacity = '1';
          tooltip.style.transform = 'translateY(0)';
        });
      },
      true
    );

    document.addEventListener(
      'mouseleave',
      function (e) {
        const element = e.target.closest('[data-tooltip]');
        if (element && tooltip) {
          tooltip.style.opacity = '0';
          setTimeout(() => {
            if (tooltip && tooltip.parentNode) {
              tooltip.parentNode.removeChild(tooltip);
            }
            tooltip = null;
          }, 150);
        }
      },
      true
    );
  }

  function createTooltip(text, position) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;

    // Style the tooltip
    Object.assign(tooltip.style, {
      position: 'absolute',
      background: '#1f2937',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '14px',
      whiteSpace: 'nowrap',
      zIndex: '9999',
      opacity: '0',
      transform: 'translateY(-4px)',
      transition: 'opacity 0.15s ease, transform 0.15s ease',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    });

    return tooltip;
  }

  function positionTooltip(tooltip, element, position) {
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    let top, left;

    switch (position) {
      case 'top':
        top = rect.top - tooltipRect.height - 8;
        left = rect.left + (rect.width - tooltipRect.width) / 2;
        break;
      case 'bottom':
        top = rect.bottom + 8;
        left = rect.left + (rect.width - tooltipRect.width) / 2;
        break;
      case 'left':
        top = rect.top + (rect.height - tooltipRect.height) / 2;
        left = rect.left - tooltipRect.width - 8;
        break;
      case 'right':
        top = rect.top + (rect.height - tooltipRect.height) / 2;
        left = rect.right + 8;
        break;
    }

    // Ensure tooltip stays within viewport
    top = Math.max(8, Math.min(top, window.innerHeight - tooltipRect.height - 8));
    left = Math.max(8, Math.min(left, window.innerWidth - tooltipRect.width - 8));

    tooltip.style.top = top + window.scrollY + 'px';
    tooltip.style.left = left + window.scrollX + 'px';
  }

  // ===========================================
  // THEME MANAGEMENT
  // ===========================================

  function initializeThemeManager() {
    const themeToggle = document.querySelector('[data-theme-toggle]');
    const currentTheme = localStorage.getItem('theme') || 'auto';

    applyTheme(currentTheme);

    if (themeToggle) {
      themeToggle.addEventListener('click', function () {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';

        applyTheme(next);
        localStorage.setItem('theme', next);

        // Animate theme transition
        document.documentElement.style.transition = 'all 0.3s ease';
        setTimeout(() => {
          document.documentElement.style.transition = '';
        }, 300);
      });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
      if (localStorage.getItem('theme') === 'auto') {
        applyTheme('auto');
      }
    });
  }

  function applyTheme(theme) {
    if (theme === 'auto') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }

    document.documentElement.setAttribute('data-theme', theme);

    // Update theme toggle icon if exists
    const themeToggle = document.querySelector('[data-theme-toggle]');
    if (themeToggle) {
      themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  }

  // ===========================================
  // NOTIFICATION SYSTEM
  // ===========================================

  function initializeNotifications() {
    // Check for browser notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Process notification queue
    setInterval(processNotificationQueue, 1000);
  }

  function showNotification(type, title, message, options = {}) {
    const notification = {
      id: generateId(),
      type: type || 'info',
      title: title || 'Notification',
      message: message || '',
      duration: options.duration || 5000,
      persistent: options.persistent || false,
      actions: options.actions || [],
    };

    notificationQueue.push(notification);

    // Also show browser notification if permission granted
    if ('Notification' in window && Notification.permission === 'granted' && options.browser) {
      new Notification(title, {
        body: message,
        icon: '/static/images/logo.png',
        tag: notification.id,
      });
    }
  }

  function processNotificationQueue() {
    if (notificationQueue.length === 0) return;

    const notification = notificationQueue.shift();
    displayToast(notification);
  }

  function displayToast(notification) {
    const toast = createToastElement(notification);
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    });

    // Auto remove unless persistent
    if (!notification.persistent) {
      setTimeout(() => {
        removeToast(toast);
      }, notification.duration);
    }
  }

  function createToastElement(notification) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${notification.type}`;
    toast.setAttribute('data-notification-id', notification.id);

    const icon = getNotificationIcon(notification.type);

    toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-header">
                    <span class="toast-icon">${icon}</span>
                    <span class="toast-title">${notification.title}</span>
                    <button class="toast-close" aria-label="Close">&times;</button>
                </div>
                <div class="toast-message">${notification.message}</div>
                ${
                  notification.actions.length > 0
                    ? `
                    <div class="toast-actions">
                        ${notification.actions
                          .map(
                            (action) => `
                            <button class="toast-action" data-action="${action.action}">
                                ${action.label}
                            </button>
                        `
                          )
                          .join('')}
                    </div>
                `
                    : ''
                }
            </div>
        `;

    // Add event listeners
    toast.querySelector('.toast-close').addEventListener('click', () => {
      removeToast(toast);
    });

    toast.querySelectorAll('.toast-action').forEach((button) => {
      button.addEventListener('click', (e) => {
        const action = e.target.getAttribute('data-action');
        handleNotificationAction(notification.id, action);
        removeToast(toast);
      });
    });

    return toast;
  }

  function removeToast(toast) {
    toast.style.transform = 'translateX(100%)';
    toast.style.opacity = '0';

    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  function getNotificationIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
    };
    return icons[type] || icons.info;
  }

  // ===========================================
  // UTILITY FUNCTIONS
  // ===========================================

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func.apply(this, args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function throttle(func, limit) {
    let inThrottle;
    return function () {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // ===========================================
  // FILE UPLOAD HANDLING
  // ===========================================

  function handleFileUpload(fileInput) {
    const files = Array.from(fileInput.files);

    files.forEach((file) => {
      // Validate file
      if (!validateFile(file)) {
        return;
      }

      // Create progress indicator
      const progressId = createUploadProgress(file);

      // Simulate upload progress
      simulateUploadProgress(progressId, () => {
        showNotification('success', 'Upload Complete', `${file.name} uploaded successfully`);
      });
    });
  }

  function validateFile(file) {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'application/pdf',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    if (file.size > maxSize) {
      showNotification(
        'error',
        'File Too Large',
        `File size must be less than ${formatFileSize(maxSize)}`
      );
      return false;
    }

    if (!allowedTypes.includes(file.type)) {
      showNotification('error', 'Invalid File Type', 'Please select a valid file type');
      return false;
    }

    return true;
  }

  function createUploadProgress(file) {
    const progressId = generateId();
    const progressElement = document.createElement('div');
    progressElement.className = 'upload-progress';
    progressElement.innerHTML = `
            <div class="upload-info">
                <span class="upload-filename">${file.name}</span>
                <span class="upload-size">${formatFileSize(file.size)}</span>
            </div>
            <div class="upload-progress-bar">
                <div class="upload-progress-fill" style="width: 0%"></div>
            </div>
            <div class="upload-status">Uploading...</div>
        `;

    const container = document.querySelector('.upload-container') || document.body;
    container.appendChild(progressElement);

    return { id: progressId, element: progressElement };
  }

  function simulateUploadProgress(progress, onComplete) {
    let percent = 0;
    const progressFill = progress.element.querySelector('.upload-progress-fill');
    const statusElement = progress.element.querySelector('.upload-status');

    const interval = setInterval(() => {
      percent += Math.random() * 15;
      if (percent >= 100) {
        percent = 100;
        clearInterval(interval);
        statusElement.textContent = 'Complete';
        progressFill.style.backgroundColor = '#10b981';

        setTimeout(() => {
          progress.element.remove();
          if (onComplete) onComplete();
        }, 1000);
      }

      progressFill.style.width = percent + '%';
    }, 200);
  }

  // ===========================================
  // MODAL FUNCTIONS
  // ===========================================

  function openSearchModal() {
    // Create or show search modal
    let modal = document.querySelector('#search-modal');
    if (!modal) {
      modal = createSearchModal();
      document.body.appendChild(modal);
    }

    modal.style.display = 'flex';
    modal.querySelector('input').focus();
  }

  function createSearchModal() {
    const modal = document.createElement('div');
    modal.id = 'search-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
            <div class="modal-content search-modal">
                <div class="search-header">
                    <input type="text" placeholder="Search projects, tasks, users..." class="search-input">
                    <button class="search-close">&times;</button>
                </div>
                <div class="search-results">
                    <!-- Search results will be populated here -->
                </div>
                <div class="search-footer">
                    <kbd>↑</kbd><kbd>↓</kbd> to navigate, <kbd>Enter</kbd> to select, <kbd>Esc</kbd> to close
                </div>
            </div>
        `;

    // Add event listeners
    modal.querySelector('.search-close').addEventListener('click', () => {
      closeModal(modal);
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal);
      }
    });

    const searchInput = modal.querySelector('.search-input');
    searchInput.addEventListener('input', debounce(performSearch, 300));

    return modal;
  }

  function performSearch(e) {
    const query = e.target.value.trim();
    const resultsContainer = document.querySelector('.search-results');

    if (query.length < 2) {
      resultsContainer.innerHTML =
        '<div class="search-hint">Type at least 2 characters to search</div>';
      return;
    }

    // Simulate search results
    const mockResults = [
      { type: 'project', title: 'Website Redesign', subtitle: 'In Progress' },
      { type: 'task', title: 'Update Homepage', subtitle: 'Due tomorrow' },
      { type: 'user', title: 'John Doe', subtitle: 'Project Manager' },
    ].filter(
      (item) =>
        item.title.toLowerCase().includes(query.toLowerCase()) ||
        item.subtitle.toLowerCase().includes(query.toLowerCase())
    );

    if (mockResults.length === 0) {
      resultsContainer.innerHTML = '<div class="search-no-results">No results found</div>';
      return;
    }

    resultsContainer.innerHTML = mockResults
      .map(
        (result) => `
            <div class="search-result-item" data-type="${result.type}">
                <span class="search-result-icon">${getSearchIcon(result.type)}</span>
                <div class="search-result-content">
                    <div class="search-result-title">${result.title}</div>
                    <div class="search-result-subtitle">${result.subtitle}</div>
                </div>
            </div>
        `
      )
      .join('');
  }

  function getSearchIcon(type) {
    const icons = {
      project: '📁',
      task: '✅',
      user: '👤',
    };
    return icons[type] || '📄';
  }

  function closeModal(modal) {
    modal.style.display = 'none';
  }

  function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach((modal) => {
      modal.style.display = 'none';
    });
  }

  function triggerNewProject() {
    // Trigger new project creation
    const newProjectButton = document.querySelector('[data-action="new-project"]');
    if (newProjectButton) {
      newProjectButton.click();
    } else {
      showNotification('info', 'New Project', 'Navigate to Projects page to create a new project');
    }
  }

  function triggerNewTask() {
    // Trigger new task creation
    const newTaskButton = document.querySelector('[data-action="new-task"]');
    if (newTaskButton) {
      newTaskButton.click();
    } else {
      showNotification('info', 'New Task', 'Navigate to Tasks page to create a new task');
    }
  }

  // ===========================================
  // FORM ENHANCEMENTS
  // ===========================================

  function autoSaveFormData(input) {
    const form = input.closest('form');
    if (!form) return;

    const formId = form.id || 'default-form';
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
      localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));

      // Show subtle save indicator
      const indicator = getOrCreateSaveIndicator(form);
      indicator.textContent = 'Saved';
      indicator.style.opacity = '1';

      setTimeout(() => {
        indicator.style.opacity = '0';
      }, 2000);
    } catch (error) {
      console.warn('Could not save form data:', error);
    }
  }

  function getOrCreateSaveIndicator(form) {
    let indicator = form.querySelector('.auto-save-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'auto-save-indicator';
      indicator.style.cssText = `
                position: absolute;
                top: -30px;
                right: 0;
                background: #10b981;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: none;
            `;
      form.style.position = 'relative';
      form.appendChild(indicator);
    }
    return indicator;
  }

  function restoreFormData(formId) {
    try {
      const saved = localStorage.getItem(`autosave_${formId}`);
      if (!saved) return;

      const data = JSON.parse(saved);
      const form = document.getElementById(formId);
      if (!form) return;

      Object.entries(data).forEach(([name, value]) => {
        const input = form.querySelector(`[name="${name}"]`);
        if (input) {
          input.value = value;
        }
      });

      showNotification('info', 'Form Restored', 'Previously saved data has been restored');
    } catch (error) {
      console.warn('Could not restore form data:', error);
    }
  }

  // ===========================================
  // NOTIFICATION ACTION HANDLERS
  // ===========================================

  function handleNotificationAction(notificationId, action) {
    switch (action) {
      case 'view':
        // Navigate to the relevant page
        console.log('Viewing notification:', notificationId);
        break;
      case 'dismiss':
        // Dismiss the notification
        console.log('Dismissing notification:', notificationId);
        break;
      case 'snooze':
        // Snooze the notification
        console.log('Snoozing notification:', notificationId);
        break;
      default:
        console.log('Unknown action:', action);
    }
  }

  // ===========================================
  // PUBLIC API
  // ===========================================

  // Expose public methods
  window.DensoProjectManager = {
    showNotification,
    applyTheme,
    openSearchModal,
    performanceMetrics: () => ({ ...performanceMetrics }),
    version: '2.0.0',
  };

  // ===========================================
  // INITIALIZATION
  // ===========================================

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
  } else {
    initializeApp();
  }

  // Reinitialize when Streamlit reruns
  if (window.streamlit) {
    window.streamlit.setComponentReady();
    window.streamlit.onDataChanged = initializeApp;
  }

  console.log('🎯 DENSO Project Manager Pro JavaScript loaded successfully');
})();

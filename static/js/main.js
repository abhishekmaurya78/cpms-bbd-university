/**
 * Campus Placement Management System (CPMS) - Core JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } else {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
      }
    }, 5000);
  });

  // 2. Demo Login Credentials Auto-Fill
  window.fillLogin = function(email, password) {
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    if (emailInput && passwordInput) {
      emailInput.value = email;
      passwordInput.value = password;
      
      // Visual Feedback Highlight
      emailInput.classList.add('border-primary');
      passwordInput.classList.add('border-primary');
      setTimeout(() => {
        emailInput.classList.remove('border-primary');
        passwordInput.classList.remove('border-primary');
      }, 1000);
    }
  };

  // 3. Register Role Switcher Toggle
  const roleSelect = document.getElementById('register-role');
  const studentFields = document.getElementById('student-fields');
  const companyFields = document.getElementById('company-fields');

  if (roleSelect && studentFields && companyFields) {
    const toggleFields = () => {
      const selectedRole = roleSelect.value;
      if (selectedRole === 'student') {
        studentFields.style.display = 'block';
        companyFields.style.display = 'none';
      } else if (selectedRole === 'company') {
        studentFields.style.display = 'none';
        companyFields.style.display = 'block';
      } else {
        studentFields.style.display = 'none';
        companyFields.style.display = 'none';
      }
    };

    roleSelect.addEventListener('change', toggleFields);
    toggleFields(); // Initial run
  }

  // 4. Quick Table Search Filter (Client-Side)
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.addEventListener('keyup', function() {
      const filter = this.value.toLowerCase();
      const rows = document.querySelectorAll('.searchable-table tbody tr');

      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }

  // 5. Update Status Modal Pre-fill
  const statusModal = document.getElementById('updateStatusModal');
  if (statusModal) {
    statusModal.addEventListener('show.bs.modal', function(event) {
      const button = event.relatedTarget;
      if (button) {
        const appId = button.getAttribute('data-app-id');
        const currentStatus = button.getAttribute('data-status');
        const currentRemarks = button.getAttribute('data-remarks') || '';

        const form = document.getElementById('updateStatusForm');
        if (form) {
          form.action = `/application/${appId}/status`;
        }

        const statusSelect = document.getElementById('modal-status-select');
        if (statusSelect && currentStatus) {
          statusSelect.value = currentStatus;
        }

        const remarksInput = document.getElementById('modal-remarks-input');
        if (remarksInput) {
          remarksInput.value = currentRemarks;
        }
      }
    });
  }
});

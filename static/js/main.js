// FoodShare Core Client-Side Logic
document.addEventListener('DOMContentLoaded', function () {
  // 1. Password visibility toggle
  const togglePassBtns = document.querySelectorAll('.toggle-password-btn');
  togglePassBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetInput = document.querySelector(this.getAttribute('data-target'));
      if (targetInput) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          this.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          targetInput.type = 'password';
          this.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  // 2. Click to fill demo credentials
  const demoChips = document.querySelectorAll('.btn-fill-demo');
  demoChips.forEach(chip => {
    chip.addEventListener('click', function () {
      const email = this.getAttribute('data-email');
      const pass = this.getAttribute('data-pass');
      const emailField = document.querySelector('#loginEmail');
      const passField = document.querySelector('#loginPassword');
      if (emailField && passField) {
        emailField.value = email;
        passField.value = pass;
        emailField.classList.add('border-success');
        setTimeout(() => emailField.classList.remove('border-success'), 1200);
      }
    });
  });

  // 3. Dynamic unread notifications badge counter
  function updateUnreadBadge() {
    const badge = document.querySelector('#notifBadge');
    if (!badge) return;
    fetch('/notifications/unread-count')
      .then(res => res.json())
      .then(data => {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.classList.remove('d-none');
        } else {
          badge.classList.add('d-none');
        }
      })
      .catch(() => {});
  }
  updateUnreadBadge();

  // 4. Request modal population
  const requestModal = document.getElementById('requestFoodModal');
  if (requestModal) {
    requestModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      if (!button) return;
      const donationId = button.getAttribute('data-donation-id');
      const donationTitle = button.getAttribute('data-donation-title');
      const maxQty = button.getAttribute('data-max-qty');
      const unit = button.getAttribute('data-unit');
      const address = button.getAttribute('data-address');
      const pickupTime = button.getAttribute('data-pickup-time');

      document.getElementById('modalDonationId').value = donationId;
      document.getElementById('modalDonationTitle').textContent = donationTitle;
      document.getElementById('modalMaxQty').textContent = `${maxQty} ${unit}`;
      document.getElementById('modalQtyInput').max = maxQty;
      document.getElementById('modalQtyUnitLabel').textContent = unit;
      document.getElementById('modalPickupInfo').textContent = `${pickupTime} | ${address}`;
    });
  }

  // 5. Quantity slider/sync if present
  const qtyInput = document.getElementById('modalQtyInput');
  if (qtyInput) {
    qtyInput.addEventListener('input', function () {
      const max = parseFloat(this.max);
      const val = parseFloat(this.value);
      if (val > max) {
        this.value = max;
      } else if (val < 0.1) {
        this.value = 0.5;
      }
    });
  }
});

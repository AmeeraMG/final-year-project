// validation.js
// Client-side form validation for Sales Intelligence
// ─────────────────────────────────────────────────

/**
 * Validates Indian phone number format: +91XXXXXXXXXX
 * Must start with +91 followed by exactly 10 digits
 * First digit after +91 must be 6, 7, 8, or 9
 */
function validatePhone(phone) {
  const pattern = /^\+91[6-9]\d{9}$/;
  return pattern.test(phone);
}

/**
 * Validates email format
 */
function validateEmail(email) {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}

/**
 * Shows an error message below a field
 */
function showError(inputId, message) {
  const input = document.getElementById(inputId);
  const errEl = document.getElementById(inputId + "-error");
  if (input) input.classList.add("error");
  if (errEl) {
    errEl.textContent = message;
    errEl.classList.add("visible");
  }
}

/**
 * Clears error message from a field
 */
function clearError(inputId) {
  const input = document.getElementById(inputId);
  const errEl = document.getElementById(inputId + "-error");
  if (input) input.classList.remove("error");
  if (errEl) errEl.classList.remove("visible");
}

/**
 * Shows alert box with a message
 * @param {string} alertId - element ID
 * @param {string} type    - 'success' | 'error' | 'info'
 * @param {string} message
 */
function showAlert(alertId, type, message) {
  const el = document.getElementById(alertId);
  if (!el) return;
  // Remove existing type classes
  el.classList.remove("alert-success", "alert-error", "alert-info", "visible");
  el.classList.add(`alert-${type}`, "visible");
  el.innerHTML = `<span>${type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️"}</span> ${message}`;
}

/**
 * Hides alert box
 */
function hideAlert(alertId) {
  const el = document.getElementById(alertId);
  if (el) el.classList.remove("visible");
}

/**
 * Validates login form fields
 * Returns true if all fields are valid
 */
function validateLoginForm() {
  let valid = true;

  const phone    = document.getElementById("phone")?.value?.trim() || "";
  const password = document.getElementById("password")?.value || "";

  clearError("phone");
  clearError("password");

  if (!validatePhone(phone)) {
    showError("phone", "Please enter a valid Indian phone number starting with +91");
    valid = false;
  }

  if (!password) {
    showError("password", "Password is required.");
    valid = false;
  }

  return valid;
}

/**
 * Validates register form fields
 * Returns true if all fields are valid
 */
function validateRegisterForm() {
  let valid = true;

  const fields = ["name", "phone", "email", "password", "shop_name", "location"];
  fields.forEach(f => clearError(f));

  const name      = document.getElementById("name")?.value?.trim()      || "";
  const phone     = document.getElementById("phone")?.value?.trim()     || "";
  const email     = document.getElementById("email")?.value?.trim()     || "";
  const password  = document.getElementById("password")?.value          || "";
  const shopName  = document.getElementById("shop_name")?.value?.trim() || "";
  const location  = document.getElementById("location")?.value?.trim()  || "";

  if (!name) {
    showError("name", "Name is required.");
    valid = false;
  }

  if (!validatePhone(phone)) {
    showError("phone", "Please enter a valid Indian phone number starting with +91");
    valid = false;
  }

  if (!validateEmail(email)) {
    showError("email", "Please enter a valid email address.");
    valid = false;
  }

  if (!password || password.length < 6) {
    showError("password", "Password must be at least 6 characters.");
    valid = false;
  }

  if (!shopName) {
    showError("shop_name", "Shop name is required.");
    valid = false;
  }

  if (!location) {
    showError("location", "Location is required.");
    valid = false;
  }

  return valid;
}

// Live validation on phone input — show hint as user types
document.addEventListener("DOMContentLoaded", () => {
  const phoneInput = document.getElementById("phone");
  if (phoneInput) {
    // Auto-prefix +91 if user starts typing without it
    phoneInput.addEventListener("blur", () => {
      let val = phoneInput.value.trim();
      if (val && !val.startsWith("+")) {
        phoneInput.value = "+91" + val;
      } else if (val === "+91") {
        phoneInput.value = "";
      }
    });

    phoneInput.addEventListener("input", () => {
      const val = phoneInput.value.trim();
      if (val.length >= 13) {
        if (!validatePhone(val)) {
          showError("phone", "Please enter a valid Indian phone number starting with +91");
        } else {
          clearError("phone");
        }
      } else {
        clearError("phone");
      }
    });
  }
});

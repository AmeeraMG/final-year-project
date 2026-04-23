// auth.js
// Handles login, registration, logout, and session management
// ─────────────────────────────────────────────────────────────

const API_BASE = "http://127.0.0.1:5000";

// ── Save user data to sessionStorage ─────────────────────────────────────────
function saveUserSession(userData) {
  sessionStorage.setItem("user", JSON.stringify(userData));
}

// ── Get user data from sessionStorage ────────────────────────────────────────
function getUserSession() {
  const data = sessionStorage.getItem("user");
  return data ? JSON.parse(data) : null;
}

// ── Clear user session ────────────────────────────────────────────────────────
function clearUserSession() {
  sessionStorage.removeItem("user");
}

// ── Redirect if not logged in ─────────────────────────────────────────────────
function requireLogin() {
  const user = getUserSession();
  if (!user) {
    window.location.href = "login.html";
    return null;
  }
  return user;
}

// ── Handle Login form submit ──────────────────────────────────────────────────
async function handleLogin(event) {
  event.preventDefault();
  hideAlert("login-alert");

  if (!validateLoginForm()) return;

  const phone    = document.getElementById("phone").value.trim();
  const password = document.getElementById("password").value;
  const btn      = document.getElementById("login-btn");

  btn.disabled    = true;
  btn.textContent = "Logging in...";

  try {
    const response = await fetch(`${API_BASE}/login`, {
      method      : "POST",
      headers     : { "Content-Type": "application/json" },
      credentials : "include",
      body        : JSON.stringify({ phone, password }),
    });

    const data = await response.json();

    if (data.success) {
      // Save user info to session storage for frontend use
      saveUserSession(data.user);
      showAlert("login-alert", "success", "Login successful! Redirecting...");
      setTimeout(() => { window.location.href = "upload.html"; }, 1000);
    } else {
      showAlert("login-alert", "error", data.message || "Login failed. Please try again.");
    }
  } catch (err) {
    showAlert("login-alert", "error", "Cannot connect to server. Make sure the backend is running.");
  } finally {
    btn.disabled    = false;
    btn.textContent = "Login";
  }
}

// ── Handle Register form submit ───────────────────────────────────────────────
async function handleRegister(event) {
  event.preventDefault();
  hideAlert("register-alert");

  if (!validateRegisterForm()) return;

  const payload = {
    name      : document.getElementById("name").value.trim(),
    phone     : document.getElementById("phone").value.trim(),
    email     : document.getElementById("email").value.trim(),
    password  : document.getElementById("password").value,
    shop_name : document.getElementById("shop_name").value.trim(),
    location  : document.getElementById("location").value.trim(),
  };

  const btn       = document.getElementById("register-btn");
  btn.disabled    = true;
  btn.textContent = "Creating account...";

  try {
    const response = await fetch(`${API_BASE}/register`, {
      method      : "POST",
      headers     : { "Content-Type": "application/json" },
      credentials : "include",
      body        : JSON.stringify(payload),
    });

    const data = await response.json();

    if (data.success) {
      showAlert("register-alert", "success", data.message + " Redirecting to login...");
      setTimeout(() => { window.location.href = "login.html"; }, 1500);
    } else {
      showAlert("register-alert", "error", data.message || "Registration failed.");
    }
  } catch (err) {
    showAlert("register-alert", "error", "Cannot connect to server. Make sure the backend is running.");
  } finally {
    btn.disabled    = false;
    btn.textContent = "Create Account";
  }
}

// ── Handle Logout ─────────────────────────────────────────────────────────────
async function handleLogout() {
  try {
    await fetch(`${API_BASE}/logout`, {
      method      : "POST",
      credentials : "include",
    });
  } catch (e) {
    // Ignore network error on logout
  }
  clearUserSession();
  window.location.href = "index.html";
}

// ── Load profile data ─────────────────────────────────────────────────────────
async function loadProfile() {
  const user = requireLogin();
  if (!user) return;

  // Try to update from backend
  try {
    const resp = await fetch(`${API_BASE}/profile`, {
      credentials: "include",
    });
    const data = await resp.json();
    if (data.success) {
      displayProfile(data.user);
      return;
    }
  } catch (e) {
    // Fall back to session storage if backend unreachable
  }

  displayProfile(user);
}

// ── Display profile data in the UI ────────────────────────────────────────────
function displayProfile(user) {
  // Set avatar initials
  const avatarEl = document.getElementById("avatar");
  if (avatarEl) {
    avatarEl.textContent = (user.name || "U").charAt(0).toUpperCase();
  }

  // Set each profile field
  const fields = {
    "profile-name"    : user.name,
    "profile-phone"   : user.phone,
    "profile-email"   : user.email,
    "profile-shop"    : user.shop_name,
    "profile-location": user.location,
  };

  for (const [id, value] of Object.entries(fields)) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || "—";
  }
}

// ── Update nav based on login state ──────────────────────────────────────────
function updateNav() {
  const user        = getUserSession();
  const navLogin    = document.getElementById("nav-login");
  const navRegister = document.getElementById("nav-register");
  const navUpload   = document.getElementById("nav-upload");
  const navProfile  = document.getElementById("nav-profile");
  const navLogout   = document.getElementById("nav-logout");

  if (user) {
    if (navLogin)    navLogin.style.display    = "none";
    if (navRegister) navRegister.style.display = "none";
    if (navUpload)   navUpload.style.display   = "list-item";
    if (navProfile)  navProfile.style.display  = "list-item";
    if (navLogout)   navLogout.style.display   = "list-item";
  } else {
    if (navLogin)    navLogin.style.display    = "list-item";
    if (navRegister) navRegister.style.display = "list-item";
    if (navUpload)   navUpload.style.display   = "none";
    if (navProfile)  navProfile.style.display  = "none";
    if (navLogout)   navLogout.style.display   = "none";
  }
}

// Run nav update on every page load
document.addEventListener("DOMContentLoaded", updateNav);

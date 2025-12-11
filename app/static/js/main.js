// app/static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
    setupPasswordToggles();
    setupPasswordStrengthMeter();
  });
  
  // ========== Password Eye Toggle ==========
  function setupPasswordToggles() {
    const buttons = document.querySelectorAll(".password-toggle");
    if (!buttons.length) return;
  
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-target");
        if (!targetId) return;
  
        const input = document.getElementById(targetId);
        if (!input) return;
  
        const icon = btn.querySelector("i");
  
        if (input.type === "password") {
          input.type = "text";
          if (icon) {
            icon.classList.remove("bi-eye");
            icon.classList.add("bi-eye-slash");
          }
        } else {
          input.type = "password";
          if (icon) {
            icon.classList.remove("bi-eye-slash");
            icon.classList.add("bi-eye");
          }
        }
      });
    });
  }
  
  // ========== Password Strength Meter (Register Page) ==========
  function setupPasswordStrengthMeter() {
    const pwdInput = document.getElementById("password");
    const bar = document.getElementById("password-strength-bar");
    const barWrapper = document.querySelector(".password-strength-bar");
    const text = document.getElementById("password-strength-text");
  
    if (!pwdInput || !bar || !barWrapper || !text) {
      return; // Only exists on register page
    }
  
    pwdInput.addEventListener("input", () => {
      const value = pwdInput.value || "";
  
      if (!value.length) {
        // Reset meter
        barWrapper.classList.add("d-none");
        bar.style.width = "0%";
        bar.className = "progress-bar";
        text.textContent = "";
        return;
      }
  
      const { score, label } = evaluatePasswordStrength(value);
  
      // Show meter
      barWrapper.classList.remove("d-none");
  
      // Score -> percent & color
      let percent = 0;
      let colorClass = "bg-danger";
  
      if (score <= 1) {
        percent = 25;
        colorClass = "bg-danger";
      } else if (score === 2) {
        percent = 50;
        colorClass = "bg-warning";
      } else if (score === 3) {
        percent = 75;
        colorClass = "bg-info";
      } else {
        percent = 100;
        colorClass = "bg-success";
      }
  
      // Reset classes & apply new
      bar.className = "progress-bar";
      bar.classList.add(colorClass);
      bar.style.width = percent + "%";
  
      text.textContent = `Strength: ${label}`;
    });
  }
  
  // Simple password strength evaluation
  function evaluatePasswordStrength(pwd) {
    let score = 0;
  
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
    if (/\d/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
  
    // Normalize to 0–4
    if (score >= 4) score = 4;
    else if (score === 3) score = 3;
    else if (score === 2) score = 2;
    else if (score === 1) score = 1;
    else score = 0;
  
    let label = "Very Weak";
    if (score === 1) label = "Weak";
    else if (score === 2) label = "Medium";
    else if (score === 3) label = "Strong";
    else if (score === 4) label = "Very Strong";
  
    return { score, label };
  }
  
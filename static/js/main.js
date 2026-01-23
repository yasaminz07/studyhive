// ===== FILE: main.js =====

// =========================
// DOM & state
// =========================
/* =========================================================
   StudyHive JavaScript – Central UI Interaction Controller
========================================================= */

console.log("StudyHive loaded");


/* =========================================================
   1) Utility Function: Check if Selector or ID Exists
========================================================= */
function exists(selector) {
    return document.querySelector(selector) || document.getElementById(selector);
}


/* =========================================================
   2) Placeholder small button interactions
========================================================= */
document.addEventListener("click", (e) => {
    if (e.target.matches(".primary-btn.small")) {
        e.preventDefault();
        alert("This is a placeholder Post button.");
    }
});


/* =========================================================
   3) Profile dropdown menu (HOME page only, not WELCOME page)
========================================================= */
const profileArea = document.querySelector(".profile-area");
const profileMenu = document.getElementById("profileMenu");

if (profileArea && profileMenu) {
    profileArea.addEventListener("click", (e) => {
        e.stopPropagation();
        profileMenu.style.display =
            profileMenu.style.display === "flex" ? "none" : "flex";
    });

    document.addEventListener("click", () => {
        profileMenu.style.display = "none";
    });
}


/* =========================================================
   4) Theme mode toggle (if present)
========================================================= */
const toggleTheme = document.getElementById("toggleTheme");

if (toggleTheme) {
    toggleTheme.addEventListener("click", () => {
        document.body.classList.toggle("light-mode");
    });
}


/* =========================================================
   5) Sign Out functionality
========================================================= */
function showSignOut() {
    const modal = document.getElementById("signOutModal");
    if (modal) modal.style.display = "flex";
}

function signOut() {
    localStorage.clear();
    window.location.href = "/";
}


/* =========================================================
   6) Report Post Modal
========================================================= */
function showReportModal() {
    document.getElementById("reportModal").style.display = "flex";
}

function hideReportModal() {
    document.getElementById("reportModal").style.display = "none";
}

function submitReport() {
    const reason = document.querySelector('input[name="reportReason"]:checked');
    if (!reason) {
        alert("Please select a report reason.");
        return;
    }

    console.log("Reported for:", reason.value);
    hideReportModal();
    alert("Thank you! Your report has been submitted.");
}


/* =========================================================
   7) Sharing Modal
========================================================= */
function showShareModal() {
    document.getElementById("shareModal").style.display = "flex";
}

function hideShareModal() {
    document.getElementById("shareModal").style.display = "none";
}

function copyPostLink() {
    navigator.clipboard.writeText(window.location.href);
    alert("Link copied!");
}

function shareToInstagram() {
    alert("Instagram sharing will be implemented");
}

function shareToX() {
    alert("Twitter sharing will be implemented");
}

function shareToSnapchat() {
    alert("Snapchat sharing will be implemented");
}

/* =========================================================
   10) Chat Messaging System (messages.html)
========================================================= */
function sendMessage() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    if (!message) return;

    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML += `
        <div class="msg-row sent"><div class="msg">${message}</div></div>
    `;
    input.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;
}


/* =========================================================
   11) Friend Selector for Messaging
========================================================= */
function selectFriend(id) {
    console.log("Friend selected:", id);

    const chatName = exists("#chatName");
    if (!chatName) return;

    const names = ["", "Yung Limo", "Raashid Noor", "Juzer Pakawala", "Kai Johnson"];
    if (names[id]) chatName.textContent = names[id];
}


/* =========================================================
   12) Chat search filter
========================================================= */
const chatSearch = document.querySelector('.chat-search');
if (chatSearch) {
    chatSearch.addEventListener('keyup', function(e) {
        let filter = e.target.value.toLowerCase();
        let chats = document.querySelectorAll('.chat-item');

        chats.forEach(chat => {
            let name = chat.querySelector('.chat-name').textContent.toLowerCase();
            let preview = chat.querySelector('.chat-preview').textContent.toLowerCase();

            chat.style.display =
                (name.includes(filter) || preview.includes(filter))
                ? ""
                : "none";
        });
    });
}

// ================= MODAL ELEMENTS =================
const loginModal = document.getElementById("loginModal");
const signupModal = document.getElementById("signupModal");
const signOutModal = document.getElementById("signOutModal");

const openLogin = document.getElementById("openLogin");
const closeLogin = document.getElementById("closeLogin");
const closeSignup = document.getElementById("closeSignup");
const forgotModal = document.getElementById("forgotModal");
const forgotPassword = document.getElementById("forgotPassword");
const closeForgot = document.getElementById("closeForgot");


// ================= MODAL OPEN / CLOSE =================
if (openLogin && loginModal) {
    openLogin.addEventListener("click", (e) => {
        e.preventDefault();
        loginModal.style.display = "flex";
    });
}

if (closeLogin && loginModal) {
    closeLogin.addEventListener("click", () => {
        loginModal.style.display = "none";
    });
}

if (closeSignup && signupModal) {
    closeSignup.addEventListener("click", () => {
        signupModal.style.display = "none";
    });
}

// ================= SWITCH BETWEEN LOGIN & SIGNUP =================
const switchToSignup = document.getElementById("switchToSignup");
const switchToLogin = document.getElementById("switchToLogin");

if (switchToSignup && loginModal && signupModal) {
    switchToSignup.addEventListener("click", function (e) {
        e.preventDefault();
        loginModal.style.display = "none";
        signupModal.style.display = "flex";
    });
}

if (switchToLogin && loginModal && signupModal) {
    switchToLogin.addEventListener("click", function (e) {
        e.preventDefault();
        signupModal.style.display = "none";
        loginModal.style.display = "flex";
    });
}

// ================= FORGOT PASSWORD =================
if (forgotPassword && forgotModal) {
    forgotPassword.addEventListener("click", function (e) {
        e.preventDefault();
        loginModal.style.display = "none";
        forgotModal.style.display = "flex";
    });
}

if (closeForgot && forgotModal) {
    closeForgot.addEventListener("click", function () {
        forgotModal.style.display = "none";
    });
}

const forgotSubmit = document.getElementById("forgotSubmit");

if (forgotSubmit) {
    forgotSubmit.addEventListener("click", async function () {
        const email = document.getElementById("forgotEmail").value.trim();

        if (!email) {
            alert("Please enter your email");
            return;
        }

        const res = await fetch("/forgot-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        const data = await res.json();

        if (data.success) {
            alert("If this email exists, a reset link has been sent.");
            forgotModal.style.display = "none";
        } else {
            alert("Something went wrong");
        }
    });
}

// ================= GET STARTED → SIGNUP POPUP =================
const getStartedBtn = document.getElementById("getStartedBtn");

if (getStartedBtn && signupModal) {
    getStartedBtn.addEventListener("click", function (e) {
        e.preventDefault();
        signupModal.style.display = "flex";
    });
}

// ================= SIGNUP =================
const signupSubmit = document.getElementById("signupSubmit");

if (signupSubmit) {
    signupSubmit.addEventListener("click", async function () {
        const firstName = document.getElementById("signupFirstName").value.trim();
        const lastName = document.getElementById("signupLastName").value.trim();
        const username = document.getElementById("signupUsername").value.trim();
        const email = document.getElementById("signupEmail").value.trim();
        const userType = document.getElementById("signupUserType").value;  
        const password = document.getElementById("signupPassword").value;
        const confirmPassword = document.getElementById("signupConfirmPassword").value;

        if (!firstName || !lastName || !username || !email || !password || !confirmPassword) {
            alert("Please fill in all fields");
            return;
        }

        if (!userType) {
            alert("Please choose Student or Tutor");
            return;
        }

        if (password !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }

        const res = await fetch("/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                firstName,
                lastName,
                username,
                email,
                password,
                userType
            })
        });

        const data = await res.json();

        if (data.success) {
            alert("Account created! You can now log in.");
            signupModal.style.display = "none";
            loginModal.style.display = "flex";
        } else {
            alert(data.error || "Signup failed");
        }
    });
}

// ================= LOGIN =================
const loginSubmit = document.getElementById("loginSubmit");

if (loginSubmit) {
    loginSubmit.addEventListener("click", async function (e) {
        e.preventDefault();

        const username = document.getElementById("loginUsername").value.trim();
        const password = document.getElementById("loginPassword").value;

        if (!username || !password) {
            alert("Enter username and password");
            return;
        }

        const res = await fetch("/login-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            window.location.href = "/home";
        } else {
            alert("Invalid username or password");
        }
    });
}


// From SIGNUP → LOGIN
if (switchToLogin && loginModal && signupModal) {
    switchToLogin.addEventListener("click", (e) => {
        e.preventDefault();
        signupModal.style.display = "none";
        loginModal.style.display = "flex";
    });
}



/* =========================================================
   15) Closing modals when clicking outside
========================================================= */
window.addEventListener("click", function(e) {
    if (e.target === loginModal) loginModal.style.display = "none";
    if (e.target === signupModal) signupModal.style.display = "none";
    if (e.target === signOutModal) signOutModal.style.display = "none";
});

// =================== PREVENT ACCIDENTAL CLOSE =================== 
if (loginModal) {
    const loginContent = loginModal.querySelector(".modal-content");
    if (loginContent) {
        loginContent.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
}


if (signupModal) {
    const signupContent = signupModal.querySelector(".modal-content");
    if (signupContent) {
        signupContent.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
}

if (signOutModal) {
    const signOutBox = signOutModal.querySelector(".modal-box");
    if (signOutBox) {
        signOutBox.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
}


/* =========================================================
   StudyHive JavaScript – Support Form
========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("supportForm");
    const spinner = document.getElementById("loadingSpinner");
    const submitBtn = document.getElementById("submitBtn");

    if (!form) return;

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        // UI start
        spinner.classList.remove("hidden");
        submitBtn.disabled = true;

        const data = {
            email: document.getElementById("email").value,
            name: document.getElementById("name").value,
            message: document.getElementById("message").value
        };

        try {
            const response = await fetch("/support", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error("Server error");
            }

            const result = await response.json();

            if (result.success) {
                showToast("Your report has been sent successfully ✔");
                form.reset();
            } else {
                showToast("Something went wrong ❌");
            }

        } catch (err) {
            console.error(err);
            showToast("Failed to submit report ❌");
        } finally {
            // UI cleanup (THIS WAS MISSING / NOT REACHED BEFORE)
            spinner.classList.add("hidden");
            submitBtn.disabled = false;
        }
    });
});

function showToast(message) {
    const toast = document.getElementById("toast");

    if (!toast) return; // safety check

    toast.textContent = message;
    toast.classList.remove("hidden");
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
            toast.classList.add("hidden");
        }, 300);
    }, 3000);
}

// =========================
// HOME SEARCH (home.html) - Juzer
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const homeForm = document.getElementById("homeSearchForm");
  const homeInput = document.getElementById("searchInput");
  const homeResults = document.getElementById("homeSearchResults");

  // Only run this on home.html (prevents errors on other pages)
  if (!homeForm || !homeInput || !homeResults) return;

  const esc = (s) =>
    (s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  function renderHomeResults(data) {
    const subjects = data.subjects || [];
    const users = data.users || [];
    const posts = data.posts || [];

    homeResults.innerHTML = `
      <div class="sr-section">
        <h3>Subjects</h3>
        ${
          subjects.length
            ? subjects.map(s => `<a class="sr-item" href="${esc(s.url)}">${esc(s.name)}</a>`).join("")
            : `<p class="sr-empty">No subjects found</p>`
        }
      </div>

      <div class="sr-section">
        <h3>People</h3>
        ${
          users.length
            ? users.map(u => `
                <div class="sr-item sr-row">
                  <a class="sr-title" href="/profile/${u.id}">@${esc(u.username)}</a>
                  <span class="sr-sub">${esc(((u.first_name||"") + " " + (u.last_name||"")).trim())}</span>
                </div>
              `).join("")
            : `<p class="sr-empty">No people found</p>`
        }
      </div>

      <div class="sr-section">
        <h3>Posts</h3>
        ${
          posts.length
            ? posts.map(p => `
                <div class="sr-item">
                  <div class="sr-title">${esc(p.title || "Untitled post")}</div>
                  <div class="sr-sub">${esc((p.body || "").slice(0, 120))}${(p.body || "").length > 120 ? "..." : ""}</div>
                  <div class="sr-meta">by ${esc(p.author || "Unknown")}</div>
                </div>
              `).join("")
            : `<p class="sr-empty">No posts found</p>`
        }
      </div>
    `;
  }

// =========================
// API calls - Juzer
// =========================

  async function doHomeSearch() {
    const q = (homeInput.value || "").trim();

    if (!q) {
      homeResults.innerHTML = "";
      return;
    }

    try {
      // uses searchAll() from api.js
      const data = await searchAll(q);
      renderHomeResults(data);
    } catch (e) {
      console.error(e);
      homeResults.innerHTML = `<p class="sr-empty">Search failed</p>`;
    }
  }

  // submit (Enter or button)
  homeForm.addEventListener("submit", (e) => {
    e.preventDefault();
    doHomeSearch();
  });

  // live search
  let t = null;
  homeInput.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(doHomeSearch, 300);
  });
});

// Index.html signup dropdown
const select = document.getElementById("signupUserType");

function updateSelectColor() {
    if (select.value === "") {
        select.style.color = "#888";  // placeholder color
    } else {
        select.style.color = "#fff";  // normal color
    }
}

updateSelectColor();
select.addEventListener("change", updateSelectColor);

homeInput.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(doHomeSearch, 300);
  });

  document.addEventListener("click", (e) => {
    if (
      !e.target.closest("#homeSearchForm") &&
      !e.target.closest("#homeSearchResults")
    ) {
      homeResults.style.display = "none";
    }
  });

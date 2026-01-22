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
        const password = document.getElementById("signupPassword").value;
        const confirmPassword = document.getElementById("signupConfirmPassword").value;

        if (!firstName || !lastName || !username || !email || !password || !confirmPassword) {
            alert("Please fill in all fields");
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
                password
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



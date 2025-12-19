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
    window.location.href = "index.html";
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
   8) Escape key closes modals
========================================================= */
document.addEventListener('keydown', (e) => {
    if (e.key === "Escape") {
        hideReportModal();
        hideShareModal();
        if (loginModal) loginModal.style.display = "none";
        if (signupModal) signupModal.style.display = "none";
    }
});

/* =========================================================
   9) Comment system — Expandable reply boxes
========================================================= */
function openComment(id) {
    event.stopPropagation();
    document.getElementById("commentBox" + id).style.display = "block";
}

function closeComment(id) {
    document.getElementById("commentBox" + id).style.display = "none";
}

function sendComment(id) {
    let input = document.getElementById("commentInput" + id);
    let text = input.value.trim();

    if (text === "") return;

    console.log("Comment submitted:", text);

    input.value = "";
}

// CLOSE COMMENT WHEN CLICKING OUTSIDE
document.addEventListener("click", function(e) {
    const commentBoxes = document.querySelectorAll(".comment-box");

    commentBoxes.forEach(box => {
        if (box.style.display === "block" && !box.contains(e.target)) {
            box.style.display = "none";
        }
    });
});

// ESC KEY CLOSE
document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const commentBoxes = document.querySelectorAll(".comment-box");
        commentBoxes.forEach(box => box.style.display = "none");
    }
});


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


/* =========================================================
   13) LOGIN MODAL
========================================================= */
const openLogin = document.getElementById("openLogin");
const closeLogin = document.getElementById("closeLogin");
const loginModal = document.getElementById("loginModal");

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


/* =========================================================
   14) SIGNUP MODAL
========================================================= */
const openSignup = document.getElementById("openSignup");
const closeSignup = document.getElementById("closeSignup");
const signupModal = document.getElementById("signupModal");

if (openSignup && signupModal) {
    openSignup.addEventListener("click", (e) => {
        e.preventDefault();
        signupModal.style.display = "flex";
    });
}
if (closeSignup && signupModal) {
    closeSignup.addEventListener("click", () => {
        signupModal.style.display = "none";
    });
}
// =================== SWITCH BETWEEN FORMS ===================
const switchToSignup = document.getElementById("switchToSignup");
const switchToLogin = document.getElementById("switchToLogin");

// From LOGIN → SIGNUP
if (switchToSignup && loginModal && signupModal) {
    switchToSignup.addEventListener("click", (e) => {
        e.preventDefault();
        loginModal.style.display = "none";
        signupModal.style.display = "flex";
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





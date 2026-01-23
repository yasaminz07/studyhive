// ===== FILE: profile-other.js =====

// =========================
// Profile editing + uploads - Nafis
//
// DOM & state
// =========================
document.addEventListener("DOMContentLoaded", () => {
    const followBtn = document.getElementById("followBtn");
    const followersCard = document.getElementById("followersBtn");
    const followersCount = document.querySelector("#followersBtn .stat-number");

    if (!followBtn || !followersCard || !followersCount) return;

    let busy = false;

    // Make the whole card clickable
    followersCard.addEventListener("click", (e) => {
        // If user clicked the actual button, let the button handler run normally
        if (e.target.closest("#followBtn")) return;

        // Otherwise, click the real button programmatically
        followBtn.click();
    });

    followBtn.addEventListener("click", async (e) => {
        e.preventDefault();

        if (busy) return;
        busy = true;

        const profileUserId = followBtn.dataset.userId;

        const res = await fetch("/api/toggle-follow", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: profileUserId })
        });

        const data = await res.json();

        let count = parseInt(followersCount.innerText, 10);

        if (data.status === "followed") {
            followersCount.innerText = count + 1;
            followBtn.innerText = "Unfollow";
        } else if (data.status === "unfollowed") {
            followersCount.innerText = count - 1;
            followBtn.innerText = "Follow";
        }

        busy = false;
    });
});

const followingBtn = document.getElementById("followingBtn");
const followingModal = document.getElementById("followingModal");
const followingList = document.getElementById("followingList");

if (followingBtn) {
    followingBtn.addEventListener("click", async () => {
        const userId = followingBtn.dataset.userId;

        followingModal.style.display = "flex";
        followingList.innerHTML = "<p style='opacity:0.7'>Loading...</p>";

        const res = await fetch(`/api/following/${userId}`);
        const users = await res.json();

        if (users.length === 0) {
            followingList.innerHTML = "<p>No following yet.</p>";
            return;
        }

        followingList.innerHTML = "";

        users.forEach(u => {
            const div = document.createElement("div");
            div.className = "follower-item";
            div.innerHTML = `
                <a href="/profile/${u.id}">
                    <strong>${u.name}</strong>
                    <span style="opacity:0.7">@${u.username}</span>
                </a>
            `;
            followingList.appendChild(div);
        });
    });
}

// =========================
// Helpers / UI
// =========================

function closeFollowingModal() {
    followingModal.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    if (input) {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                doSearch();
            }
        });
    }
});

function doSearch() {
    const q = document.getElementById("searchInput").value.trim();
    if (!q) return;

    searchUsers(q).then(users => {
        const box = document.getElementById("searchResults");
        box.innerHTML = "";

        if (users.length === 0) {
            box.innerHTML = "<p>No users found.</p>";
            return;
        }

        users.forEach(u => {
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.justifyContent = "space-between";
            row.style.alignItems = "center";
            row.style.padding = "10px";
            row.style.borderBottom = "1px solid #ddd";

            row.innerHTML = `
                <span style="cursor:pointer" onclick="openProfile(${u.id})">
                    <strong>${u.first_name} ${u.last_name}</strong>
                    <span style="color:gray">@${u.username}</span>
                </span>
                <button onclick="toggleFollow(${u.id}, ${u.is_following})">
                    ${u.is_following ? "Unfollow" : "Follow"}
                </button>
            `;

            box.appendChild(row);
        });
    });
}

function openProfile(userId) {
    window.location.href = `/profile-other?id=${userId}`;
}

function toggleFollow(userId, isFollowing) {
    if (isFollowing) {
        unfollowUser(userId).then(() => doSearch());
    } else {
        followUser(userId).then(() => doSearch());
    }
}

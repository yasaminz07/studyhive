// ===== FILE: explore.js =====

// =========================
// DOM & state
// =========================
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
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("exploreSearchForm");
  const input = document.getElementById("exploreSearchInput");
  const box = document.getElementById("searchResults");

  if (!form || !input || !box) return;

  const esc = (s) =>
    (s || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  function render(data) {
    const subjects = data.subjects || [];
    const users = data.users || [];
    const posts = data.posts || [];

    box.innerHTML = `
      <div class="sr-section">
        <h3>Subjects</h3>
        ${subjects.length ? subjects.map(s => `<a class="sr-item" href="${esc(s.url)}">${esc(s.name)}</a>`).join("") : `<p class="sr-empty">No subjects found</p>`}
      </div>

      <div class="sr-section">
        <h3>People</h3>
        ${users.length ? users.map(u => `
          <div class="sr-item sr-row">
            <a class="sr-title" href="/profile/${u.id}">@${esc(u.username)}</a>
            <span class="sr-sub">${esc(((u.first_name||"") + " " + (u.last_name||"")).trim())}</span>
          </div>
        `).join("") : `<p class="sr-empty">No people found</p>`}
      </div>

      <div class="sr-section">
        <h3>Posts</h3>
        ${posts.length ? posts.map(p => `
          <div class="sr-item">
            <div class="sr-title">${esc(p.title || "Untitled post")}</div>
            <div class="sr-sub">${esc((p.body || "").slice(0, 120))}${(p.body || "").length > 120 ? "..." : ""}</div>
            <div class="sr-meta">by ${esc(p.author || "Unknown")}</div>
          </div>
        `).join("") : `<p class="sr-empty">No posts found</p>`}
      </div>
    `;
  }

// =========================
// API calls
// =========================

  async function doSearch() {
    const q = (input.value || "").trim();
    if (!q) { box.innerHTML = ""; return; }

    const data = await searchAll(q); // from api.js
    render(data);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    doSearch();
  });

  let t = null;
  input.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(doSearch, 300);
  });
});

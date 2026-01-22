let page = 1;
let loading = false;
let noMorePosts = false;

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadCommentCount(postId) {
    const res = await fetch(`/posts/${postId}/comments/count`);
    const data = await res.json();
    return data.count;
}

async function loadPosts() {
  if (loading || noMorePosts) return;
  loading = true;

  const loadingEl = document.getElementById("loading");
  if (loadingEl) loadingEl.style.display = "block";

  const res = await fetch(`/api/posts?page=${page}`, { credentials: "same-origin" });
  const posts = await res.json();

  if (!Array.isArray(posts) || posts.length === 0) {
    noMorePosts = true;
    if (loadingEl) loadingEl.innerText = "No more posts.";
    return;
  }

  const feed = document.getElementById("feed");
  if (!feed) return;

  posts.forEach((p) => {
    const post = document.createElement("article");
    post.className = "post-card";
    post.dataset.postId = p.id;

    const author = escapeHtml(p.author);
    const createdAt = escapeHtml(p.created_at);
    const title = escapeHtml(p.title);
    const body = escapeHtml(p.body);

    const avatarHtml = p.profile_image
      ? `<img src="${escapeHtml(p.profile_image)}" class="post-avatar-img" alt="avatar">`
      : `<div class="avatar-circle purple post-avatar-fallback">${escapeHtml(p.initials)}</div>`;

    post.innerHTML = `
      <header class="post-header">
        <div class="post-author">
          ${avatarHtml}
          <div>
            <a href="/profile/${p.user_id}" class="author-name">${author}</a>
            <div class="post-meta">${createdAt}</div>
          </div>
        </div>
      </header>

      <div class="post-body">
        <h3 class="post-title">${title}</h3>
        <p class="post-text">${body}</p>
      </div>

      <footer class="post-footer">
        <button class="post-stat">♡</button>
        <button class="post-stat comment-btn" data-post-id="${p.id}">
          💬 <span class="comment-count">0</span>
        </button>
        <button class="post-stat">🔖</button>
        <button class="post-stat">⤴</button>
      </footer>

      <div class="comments-panel" id="comments-panel-${p.id}" style="display:none;">
        <div class="comments-list" id="comments-list-${p.id}">
          <div style="opacity:.6;">Loading comments…</div>
        </div>

        <form class="comment-form" data-post-id="${p.id}">
          <input
            type="text"
            class="comment-input"
            placeholder="Write a comment…"
            maxlength="500"
            required
          />
          <button type="submit">Post</button>
        </form>
      </div>
    `;

    feed.appendChild(post);
    loadCommentCount(p.id).then(count => {
      const span = post.querySelector(".comment-btn .comment-count");
      if (span) span.textContent = count;
    });
  });

  page++;
  loading = false;
}

/* ===============================
   INFINITE SCROLL
================================ */
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 400) {
    loadPosts();
  }
});

/* ===============================
   RESET FEED (used after posting)
================================ */
window.resetFeed = function () {
  page = 1;
  loading = false;
  noMorePosts = false;

  const feed = document.getElementById("feed");
  if (feed) feed.innerHTML = "";

  const loadingEl = document.getElementById("loading");
  if (loadingEl) {
    loadingEl.innerText = "Loading more posts...";
    loadingEl.style.display = "block";
  }

  loadPosts();
};

loadPosts();

// ===============================
// HELPERS
// ===============================
function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatTime(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleString(); }
  catch { return ""; }
}

// ===============================
// LOAD COMMENTS
// ===============================
async function loadComments(postId) {
  const list = document.getElementById(`comments-list-${postId}`);
  if (!list) return;

  list.innerHTML = `<div style="opacity:.6;">Loading comments...</div>`;

  const res = await fetch(`/posts/${postId}/comments`, { credentials: "same-origin" });
  if (!res.ok) {
    list.innerHTML = `<div style="opacity:.6;">Failed to load comments</div>`;
    return;
  }

  const comments = await res.json();

  if (!Array.isArray(comments) || comments.length === 0) {
    list.innerHTML = `<div style="opacity:.6;">No comments yet</div>`;
    return;
  }

  list.innerHTML = "";
  comments.forEach(c => {
    const div = document.createElement("div");
    div.className = "comment-row";
    div.innerHTML = `
      <div style="display:flex; gap:8px;">
        <img src="${escapeHtml(c.profile_image || "/static/assets/profile.png")}" class="comment-avatar">
        <div>
          <strong>${escapeHtml(c.username)}</strong>
          <div style="opacity:.7; font-size:12px;">${formatTime(c.created_at)}</div>
          <div>${escapeHtml(c.content)}</div>
        </div>
      </div>
    `;
    list.appendChild(div);
  });

  updateCommentCount(postId, comments.length);
}

// ===============================
// COMMENT COUNT
// ===============================
function updateCommentCount(postId, count) {
  const span = document.querySelector(`.comment-btn[data-post-id="${postId}"] .comment-count`);
  if (!span) return;
  span.textContent = count;
}

// ===============================
// TOGGLE COMMENTS
// ===============================
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".comment-btn");
  if (!btn) return;

  const postId = btn.dataset.postId;
  const panel = document.getElementById(`comments-panel-${postId}`);
  if (!panel) return;

  const open = panel.style.display === "block";
  panel.style.display = open ? "none" : "block";

  if (!open) {
    await loadComments(postId);
  }
});

// ===============================
// SUBMIT COMMENT
// ===============================
document.addEventListener("submit", async (e) => {
  const form = e.target.closest(".comment-form");
  if (!form) return;

  e.preventDefault();

  const postId = form.dataset.postId;
  const input = form.querySelector(".comment-input");
  const content = input.value.trim();
  if (!content) return;

  const res = await fetch(`/posts/${postId}/comments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({ content })
  });

  const data = await res.json();

  if (!res.ok || data.success === false) {
    alert(data.error || "Failed to post comment");
    return;
  }

  input.value = "";
  await loadComments(postId);
});

// ===== FILE: posts.js =====

// =========================
// DOM & state
// =========================
let page = 1;
let loading = false;
let noMorePosts = false;

/* ===============================
   UTIL
================================ */
function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// Load comment count for one post
async function loadCommentCount(postId) {
  try {
    const res = await fetch(`/posts/${postId}/comments`, { credentials: "same-origin" });
    if (!res.ok) return 0;
    const comments = await res.json();
    if (!Array.isArray(comments)) return 0;
    return comments.length;
  } catch (e) {
    console.error("Count fetch failed for post", postId, e);
    return 0;
  }
}

function formatTime(iso) {
  if (!iso) return "";
  try { return new Date(iso).toLocaleString(); }
  catch { return ""; }
}

/* ===============================
   IMAGE EXPAND MODAL - Nafis
================================ */
function ensureImageModal() {
  if (document.getElementById("imageModal")) return;

  const modal = document.createElement("div");
  modal.id = "imageModal";
  modal.className = "image-modal";
  modal.innerHTML = `
    <div class="image-modal-inner">
      <button class="image-modal-close">✕</button>
      <img class="image-modal-img" alt="Expanded image">
    </div>
  `;

  document.body.appendChild(modal);

  const close = () => modal.classList.remove("show");

  modal.addEventListener("click", (e) => {
    if (e.target === modal) close();
  });

  modal.querySelector(".image-modal-close").addEventListener("click", close);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });
}

function openImageModal(src) {
  ensureImageModal();
  const modal = document.getElementById("imageModal");
  const img = modal.querySelector(".image-modal-img");
  img.src = src;
  modal.classList.add("show");
}

/* ===============================
   COMMENTS SYSTEM (MERGED)
================================ */

// Load comments
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
    updateCommentCount(postId, 0);
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

// Update comment counter
function updateCommentCount(postId, count) {
  const span = document.querySelector(`.comment-btn[data-post-id="${postId}"] .comment-count`);
  if (!span) return;
  span.textContent = count;
}

// Toggle comments panel
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

// Submit comment
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

/* ===============================
   LOAD POSTS
================================ */

// =========================
// API calls - Yasamin
// =========================
async function loadPosts() {
  const feed = document.getElementById("feed");
  if (!feed) return;

  if (loading || noMorePosts) return;
  loading = true;

  const loadingEl = document.getElementById("loading");
  if (loadingEl) loadingEl.style.display = "block";

  let url = `/api/posts?page=${page}`;

  if (window.PROFILE_USER_ID) {
    url = `/api/posts?page=${page}&user_id=${window.PROFILE_USER_ID}`;
  }

  const res = await fetch(url, { credentials: "same-origin" });
  const posts = await res.json();

  if (!Array.isArray(posts) || posts.length === 0) {
    noMorePosts = true;
    if (loadingEl) loadingEl.innerText = "No more posts.";
    loading = false;
    return;
  }

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
      : `<div class="avatar-circle purple post-avatar-fallback">${escapeHtml(p.initials || "U")}</div>`;

    const imageHtml = p.image_url
      ? `
        <div class="post-placeholder">
          <div class="post-image-wrapper">
            <img
              src="${escapeHtml(p.image_url)}"
              class="post-image clickable"
              data-expand-src="${escapeHtml(p.image_url)}"
              alt="post image"
            >
          </div>
        </div>
      `
      : "";

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
        ${imageHtml}
      </div>

      <footer class="post-footer">
        <img src="/static/img/like.png" class="post-stat">

        <button class="post-stat comment-btn" data-post-id="${p.id}">
          <img src="/static/img/comment.png" class="comment-icon">
          <span class="comment-count">0</span>
        </button>

        <img src="/static/img/bookmark.png" class="post-stat">
        <img src="/static/img/share.png" class="post-stat">
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
    // Load comment count immediately
    loadCommentCount(p.id).then(count => {
      const span = post.querySelector(".comment-btn .comment-count");
      if (span) span.textContent = count;
    });
  });

  // bind image expand clicks
  document.querySelectorAll(".post-image.clickable").forEach((img) => {
    if (img.dataset.bound) return;
    img.dataset.bound = "1";
    img.addEventListener("click", () => {
      openImageModal(img.dataset.expandSrc || img.src);
    });
  });

  page++;
  loading = false;
}

/* ===============================
   INFINITE SCROLL - Yasamin
================================ */
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 400) {
    loadPosts();
  }
});

/* ===============================
   RESET FEED
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

/* ===============================
   CREATE POST MODAL - Ismaeel
================================ */
function showCreatePost() {
  const modal = document.getElementById("createPostModal");
  if (!modal) return;
  modal.style.display = "flex";
}

function hideCreatePost() {
  const modal = document.getElementById("createPostModal");
  if (!modal) return;
  modal.style.display = "none";
}

/* ===============================
   CREATE POST (IMAGE UPLOAD)
================================ */
async function submitPost() {
  const titleEl = document.getElementById("postTitle");
  const bodyEl = document.getElementById("postBody");
  const fileInput = document.getElementById("postImage");

  if (!titleEl || !bodyEl) return; 
  const title = titleEl.value.trim();
  const body = bodyEl.value.trim();
  const file = fileInput?.files?.[0] || null;

  if (!title || !body) {
    alert("Please fill in all fields");
    return;
  }

  const form = new FormData();
  form.append("title", title);
  form.append("body", body);
  if (file) form.append("image", file);

  const res = await fetch("/api/posts", {
    method: "POST",
    credentials: "include",
    body: form
  });

  if (res.ok) {
    hideCreatePost();
    titleEl.value = "";
    bodyEl.value = "";
    if (fileInput) fileInput.value = "";
    window.resetFeed();
  } else {
    let err = {};
    try { err = await res.json(); } catch {}
    alert("Failed to create post: " + (err.error || "Unknown error"));
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const modal = document.getElementById("createPostModal");
    if (modal) hideCreatePost();
  }
});

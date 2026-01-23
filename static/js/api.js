// ===== FILE: api.js =====

// =========================
// DOM & state
// =========================
// Helper: Base URL of the backend
const BASE_URL = "http://127.0.0.1:5000";

/**
 * Search People + Posts + Subjects
 * GET /api/search?q=...
 */

// =========================
// Helpers / UI
// =========================
function searchAll(query) {
  return fetch(`${BASE_URL}/api/search?q=${encodeURIComponent(query)}`, {
    method: "GET",
    credentials: "include",
  })
    .then((r) => r.json())
    .catch((e) => console.error("Search Error:", e));
}

/**
 * Toggle follow/unfollow
 * POST /api/toggle-follow  { user_id: <targetId> }
 */
function toggleFollow(userId) {
  return fetch(`${BASE_URL}/api/toggle-follow`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ user_id: userId }),
  })
    .then((r) => r.json())
    .catch((e) => console.error("Toggle Follow Error:", e));
}

/**
 * Get following list (you already have this endpoint)
 * GET /api/following/<user_id>
 */
function getFollowing(userId) {
  return fetch(`${BASE_URL}/api/following/${userId}`, {
    method: "GET",
    credentials: "include",
  })
    .then((r) => r.json())
    .catch((e) => console.error("Get Following Error:", e));
}

/**
 * Get a user's profile + follow stats
 * GET /api/users/<user_id>
 */
function getUserProfile(userId) {
  return fetch(`${BASE_URL}/api/users/${userId}`, {
    method: "GET",
    credentials: "include",
  })
    .then((r) => r.json())
    .catch((e) => console.error("Get User Profile Error:", e));
}

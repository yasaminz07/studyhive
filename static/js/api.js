// Helper: Base URL of the backend
const BASE_URL = "http://127.0.0.1:5000";

// API: Search users by query
function searchUsers(query) {
    return fetch(`${BASE_URL}/api/users/search?q=${query}`, {
        method: "GET",
        credentials: "include",
    })
    .then(response => response.json())
    .catch(error => console.error("Search Users Error:", error));
}

// API: Follow a user by user ID
function followUser(userId) {
    return fetch(`${BASE_URL}/api/follow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ userId: userId }),
    })
    .then(response => response.json())
    .catch(error => console.error("Follow User Error:", error));
}

// API: Unfollow a user by user ID
function unfollowUser(userId) {
    return fetch(`${BASE_URL}/api/unfollow`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ userId: userId }),
    })
    .then(response => response.json())
    .catch(error => console.error("Unfollow User Error:", error));
}

// API: Get followers of a user
function getFollowers(userId) {
    return fetch(`${BASE_URL}/api/followers/${userId}`, {
        method: "GET",
        credentials: "include",
    })
    .then(response => response.json())
    .catch(error => console.error("Get Followers Error:", error));
}

// API: Get following of a user
function getFollowing(userId) {
    return fetch(`${BASE_URL}/api/following/${userId}`, {
        method: "GET",
        credentials: "include",
    })
    .then(response => response.json())
    .catch(error => console.error("Get Following Error:", error));
}

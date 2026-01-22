document.getElementById("saveProfileBtn").addEventListener("click", async () => {
  const firstName = document.getElementById("epFirstName").value.trim();
  const lastName = document.getElementById("epLastName").value.trim();
  const username = document.getElementById("epUsername").value.trim();
  const email = document.getElementById("epEmail").value.trim();
  const fileInput = document.getElementById("profileImageInput");

  // 1) Update text fields
  const res = await fetch("/api/me", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      username: username,
      email: email
    })
  });

  const data = await res.json();
  if (!res.ok || !data.success) {
    alert(data.error || "Failed to update profile");
    return;
  }

  // 2) Upload image if selected
  if (fileInput.files.length > 0) {
    const formData = new FormData();
    formData.append("image", fileInput.files[0]);

    const imgRes = await fetch("/api/me/profile-image", {
      method: "POST",
      body: formData,
      credentials: "same-origin"
    });

    const imgData = await imgRes.json();
    if (!imgRes.ok || !imgData.success) {
      alert(imgData.error || "Image upload failed");
      return;
    }

    // Update all images on page
    document.querySelectorAll("img.profile-icon").forEach(img => {
      img.src = imgData.profile_image + "?t=" + Date.now(); // cache bust
    });
  }

  alert("Profile updated successfully!");
  document.getElementById("editProfileModal").style.display = "none";
});

document.getElementById("closeEditProfile").onclick = () => {
  document.getElementById("editProfileModal").style.display = "none";
};

const editBtn = document.getElementById("editProfileBtn");
const modal = document.getElementById("editProfileModal");

editBtn.addEventListener("click", async () => {
  modal.style.display = "flex";

  const res = await fetch("/api/me", { credentials: "same-origin" });
  const data = await res.json();

  if (!data.success) return;

  document.getElementById("epFirstName").value = data.first_name || "";
  document.getElementById("epLastName").value = data.last_name || "";
  document.getElementById("epUsername").value = data.username || "";
  document.getElementById("epEmail").value = data.email || "";
});

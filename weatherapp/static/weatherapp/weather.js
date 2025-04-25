document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("darkModeToggle");
  
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        console.log("✅ Toggle button clicked");
        document.body.classList.toggle("dark-mode");
      });
    } else {
      console.error("❌ Toggle button not found");
    }
  });
  
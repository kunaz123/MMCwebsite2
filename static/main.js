// Paste your JS here
document.addEventListener("DOMContentLoaded", () => {

  // ------------------ Rank Bars ------------------
  const rankBars = document.querySelectorAll(".rank-bar > div");
  rankBars.forEach(bar => {
    const width = bar.dataset.score || 0;
    bar.style.width = width + "%";
  });

  // ------------------ Event Animation ------------------
  const eventItems = document.querySelectorAll(".event-item");
  eventItems.forEach((item, index) => {
    item.style.opacity = 0;
    item.style.transform = "translateY(20px)";
    setTimeout(() => {
      item.style.transition = "all 0.6s ease-out";
      item.style.opacity = 1;
      item.style.transform = "translateY(0)";
    }, index * 150);
  });

  // ------------------ Profile Picture Preview ------------------
  const profileInput = document.querySelector('input[name="profile_pic"]');
  if (profileInput) {
    profileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(event) {
        const img = document.querySelector(".avatar-large");
        if (img) img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

  // ------------------ Clan Logo Preview ------------------
  const clanInput = document.querySelector('input[name="logo"]');
  if (clanInput) {
    clanInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(event) {
        const img = document.querySelector(".clan-logo-preview");
        if (img) img.src = event.target.result;
      };
      reader.readAsDataURL(file);
    });
  }

});

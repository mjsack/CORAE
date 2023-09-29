document.addEventListener("DOMContentLoaded", function () {
  const settingsButtons = document.querySelectorAll(
    '[data-bs-toggle="collapse"]'
  );

  settingsButtons.forEach((btn) => {
    const target = document.querySelector(btn.getAttribute("data-bs-target"));
    const icon = btn.querySelector(".bi.bi-chevron-down, .bi.bi-chevron-up");

    if (!icon) return;

    target.addEventListener("show.bs.collapse", function () {
      icon.classList.remove("bi-chevron-down");
      icon.classList.add("bi-chevron-up");
    });

    target.addEventListener("hide.bs.collapse", function () {
      icon.classList.remove("bi-chevron-up");
      icon.classList.add("bi-chevron-down");
    });
  });

  const deleteBtns = document.querySelectorAll(".btn-danger");
  deleteBtns.forEach((deleteBtn) => {
    let timeout;

    deleteBtn.addEventListener("click", function (e) {
      e.preventDefault();

      if (deleteBtn.classList.contains("btn-danger")) {
        deleteBtn.innerHTML = '<i class="bi bi-check"></i>';
        deleteBtn.classList.remove("btn-danger");
        deleteBtn.classList.add("btn-success");

        timeout = setTimeout(function () {
          deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
          deleteBtn.classList.add("btn-danger");
          deleteBtn.classList.remove("btn-success");
        }, 5000);
      } else {
        clearTimeout(timeout);
        e.target.closest("form").submit();
      }
    });
  });

  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("alert-slide-out");

      alert.addEventListener("transitionend", function handler() {
        let bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
        alert.removeEventListener("transitionend", handler);
      });
    }, 5000);
  });
});

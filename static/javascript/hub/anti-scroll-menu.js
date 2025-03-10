document.addEventListener("DOMContentLoaded", function () {
    const menu = document.getElementById("right-menu");
    const menuToggle = document.querySelector(".hamburger"); // Your hamburger button

    function closeMenu() {
        if (menu.classList.contains("open")) {
            menu.classList.remove("open"); // Close the menu
            menuToggle.classList.remove("open"); // Reset hamburger icon
        }
    }

    // Toggle menu on hamburger click
    menuToggle.addEventListener("click", function () {
        menu.classList.toggle("open");
        menuToggle.classList.toggle("open"); // Toggle hamburger animation
    });

    // Close menu on scroll
    window.addEventListener("scroll", closeMenu);
});

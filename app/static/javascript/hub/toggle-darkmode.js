document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.getElementById("dark-mode-toggle");
    const sunIcon = toggleButton.querySelector('.sun');
    const moonIcon = toggleButton.querySelector('.moon');
    const body = document.body;

    // Debugging
    console.log("Initial darkMode value:", localStorage.getItem("darkMode"));
    
    // Check local storage for dark mode preference
    if (localStorage.getItem("darkMode") === "enabled") {
        body.classList.add("dark-mode");
        sunIcon.style.display = "none";
        moonIcon.style.display = "inline";
        console.log("Applied dark mode on load");
    } else {
        console.log("Keeping light mode on load");
    }

    toggleButton.addEventListener("click", () => {
        if (body.classList.contains("dark-mode")) {
            body.classList.remove("dark-mode");
            localStorage.setItem("darkMode", "disabled");
            sunIcon.style.display = "inline";
            moonIcon.style.display = "none";
            console.log("Switched to light mode");
        } else {
            body.classList.add("dark-mode");
            localStorage.setItem("darkMode", "enabled");
            sunIcon.style.display = "none";
            moonIcon.style.display = "inline";
            console.log("Switched to dark mode");
        }
        
        // Debugging
        console.log("Current darkMode value:", localStorage.getItem("darkMode"));
        console.log("Body has dark-mode class:", body.classList.contains("dark-mode"));
    });
});
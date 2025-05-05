document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".reveal-button");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const sectionId = button.getAttribute("data-content") + "-info";
            const section = document.getElementById(sectionId);

            if (section) {
                // Toggle the hidden-stat class
                section.classList.toggle("hidden-stat");
                
                // Toggle button text
                button.textContent = section.classList.contains("hidden-stat") ? "Reveal" : "Hide";
                
                // Smooth scroll to the section if revealing
                if (!section.classList.contains("hidden-stat")) {
                    section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } else {
                console.error(`Section with ID ${sectionId} not found.`);
            }
        });
        
        // Initialize button text based on current state
        const sectionId = button.getAttribute("data-content") + "-info";
        const section = document.getElementById(sectionId);
        if (section && section.classList.contains("hidden-stat")) {
            button.textContent = "Reveal";
        } else if (section) {
            button.textContent = "Hide";
        }
    });
});
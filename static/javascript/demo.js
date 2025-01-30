document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".reveal-button");

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const sectionId = button.getAttribute("data-content") + "-info";
            const section = document.getElementById(sectionId);

            if (section) {
                section.classList.toggle("hidden-stat");
                button.textContent = section.classList.contains("hidden-stat") ? "Reveal" : "Hide";
            } else {
                console.error(`Section with ID ${sectionId} not found.`);
            }
        });
    });

    // Common Modal Elements
    const pinModal = document.getElementById('pin-modal');
    const pinInput = document.getElementById('pin-input');
    const submitPinBtn = document.getElementById('submit-pin-btn');
    const cancelPinBtn = document.getElementById('cancel-pin-btn');

    // Correct PIN
    const correctPin = '123456';

    // Handle PIN submission
    submitPinBtn.addEventListener('click', () => {
        const enteredPin = pinInput.value.trim();
        if (enteredPin === correctPin) {
            const section = pinInput.dataset.section;
            if (section) {
                document.getElementById(section + '-info').classList.remove('hidden-stat');
                const revealButton = document.querySelector(`[data-content="${section}"]`);
                if (revealButton) {
                    revealButton.textContent = 'Hide';
                }
            }
            pinModal.style.display = 'none';
        } else {
            alert('Incorrect PIN. Please try again.');
        }
    });

    // Cancel and close the modal
    cancelPinBtn.addEventListener('click', () => {
        pinModal.style.display = 'none';
    });

    // Close modal when clicking outside it
    pinModal.addEventListener('click', (event) => {
        if (event.target === pinModal) {
            pinModal.style.display = 'none';
        }
    });

    // Function to show PIN modal
    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const section = button.getAttribute("data-content");
            if (section === 'payment') { // PIN required only for payment section
                pinModal.style.display = 'flex';
                pinInput.value = '';
                pinInput.dataset.section = section;
                pinInput.focus();
            }
        });
    });
});

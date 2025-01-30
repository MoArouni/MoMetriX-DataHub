let isPinVerified = false;  // Track PIN verification status

// Function to verify PIN input
function verifyPin() {
    const pinInput = document.getElementById('pin');
    const enteredPin = pinInput.value;
    const messageContainer = document.getElementById('pin-message'); // The message container

    // Clear any previous message
    messageContainer.style.display = 'block';
    messageContainer.classList.remove('error', 'success');
    
    // Example PIN check (replace '1234' with the actual PIN)
    if (enteredPin === '1234') {
        // Set PIN verification status to true
        isPinVerified = true;

        // Reveal the content and show hide button
        document.querySelector('#product-info').style.display = 'block';
        document.querySelector('#pin-container').style.display = 'none';  // Hide PIN input
        document.querySelector('#confidential-message').style.display = 'none';  // Hide confidential message
        document.querySelector('#hide-button').style.display = 'block';  // Show hide button

        // Display success message
        messageContainer.textContent = 'PIN correct! Content revealed.';
        messageContainer.classList.add('success');  // Add success styling

        // Clear the PIN input field after submission
        pinInput.value = '';  // This clears the input field
    } else {
        // Display error message
        messageContainer.textContent = 'Incorrect PIN. Please try again.';
        messageContainer.classList.add('error');  // Add error styling
    }
}

// Function to hide content when Hide button is clicked
function hideContent() {
    // Hide the content and reset everything
    document.querySelector('#product-info').style.display = 'none';
    document.querySelector('#hide-button').style.display = 'none';  // Hide the hide button
    document.querySelector('#pin-container').style.display = 'block';  // Show PIN input again
    document.querySelector('#confidential-message').style.display = 'block';  // Show confidential message
    isPinVerified = false;  // Reset PIN verification status

    // Clear any previous message
    const messageContainer = document.getElementById('pin-message');
    messageContainer.style.display = 'none';  // Hide the message after hiding the content
}

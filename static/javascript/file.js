document.addEventListener('DOMContentLoaded', function () {
    const customUploadButton = document.getElementById('custom-upload-button');
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('file-name');
    const submitButton = document.getElementById('submit-button');

    // When the custom upload button is clicked, trigger the file input click event
    customUploadButton.addEventListener('click', () => {
        fileInput.click(); // Opens file dialog when custom button is clicked
    });

    // When a file is selected, update the file name and enable the submit button
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name; // Show selected file name
            submitButton.disabled = false; // Enable the submit button
        } else {
            fileNameDisplay.textContent = 'No file selected'; // Show "No file selected" if no file chosen
            submitButton.disabled = true; // Keep submit button disabled if no file is selected
        }
    });
});

// Trigger the file input when custom button is clicked
document.getElementById('custom-upload-button').addEventListener('click', function() {
    document.getElementById('file').click();
});

// Update the display name when a file is selected
document.getElementById('file').addEventListener('change', function() {
    var fileName = this.files.length > 0 ? this.files[0].name : 'No file selected';
    document.getElementById('file-name').textContent = fileName;

    // Enable the submit button if a file is selected
    document.getElementById('submit-button').disabled = false;
});

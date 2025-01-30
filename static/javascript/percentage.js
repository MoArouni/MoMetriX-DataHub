document.getElementById('percentage-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent form submission

    const value = parseFloat(document.getElementById('value').value);
    const total = parseFloat(document.getElementById('total').value);
    const result = document.getElementById('result');

    if (!isNaN(value) && !isNaN(total) && total !== 0) {
        const percentage = ((value / total) * 100).toFixed(2);
        result.textContent = `Result: ${percentage}%`;
    } else {
        result.textContent = 'Invalid input!';
    }
});

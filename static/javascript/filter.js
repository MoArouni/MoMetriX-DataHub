document.addEventListener('DOMContentLoaded', () => {
    const filterForm = document.getElementById('filter-form');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    // Function to parse date in mm/dd/yyyy format
    function parseDate(dateString) {
        const parts = dateString.split('/');
        const month = parseInt(parts[0], 10) - 1; // Months are zero-based in JavaScript Date
        const day = parseInt(parts[1], 10);
        const year = parseInt(parts[2], 10);
        return new Date(year, month, day);
    }

    // Function to handle form validation
    function validateFilters() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        // If both dates are provided, check if start date is before end date
        if (startDate && endDate) {
            const formattedStartDate = parseDate(startDate);
            const formattedEndDate = parseDate(endDate);

            if (formattedStartDate > formattedEndDate) {
                alert("Start date must be before end date.");
                return false;
            }
        }

        // Ensure at least one date is provided
        if (!startDate && !endDate) {
            alert("Please select at least a start date or an end date.");
            return false;
        }

        return true;
    }

    // Handle form submission
    filterForm.addEventListener('submit', (event) => {
        if (!validateFilters()) {
            event.preventDefault();  // Prevent form submission if validation fails
        }
    });

    // Optional: Event listener to handle dynamic input changes (e.g., reset filters on form reset)
    filterForm.addEventListener('reset', () => {
        // Optional: Reset any dynamic UI updates or inputs here
        console.log('Form has been reset');
    });
});

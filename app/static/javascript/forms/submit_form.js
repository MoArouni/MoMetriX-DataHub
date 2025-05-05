// ... (your generateRows(), updateCategories(), updateSetType(), updateExtraDetails() functions) ...

function validateForm() {
    const rows = document.querySelectorAll('.row');
    for (let i = 0; i < rows.length; i++) {
        let row = rows[i];
        // Check standard required fields:
        let month = row.querySelector('[name="month"]').value;
        let dayOfWeek = row.querySelector('[name="day_of_week"]').value;
        let dayOfSale = row.querySelector('[name="day_of_sale"]').value.trim();
        let productType = row.querySelector('[name="product_type"]').value;
        let category = row.querySelector('[name="category"]').value;
        let extraDetail = row.querySelector('[name="extra_detail"]').value
        
        // Verify that required fields have a non-empty value
        if (!month) {
            alert(`Please select a month in row ${i + 1}.`);
            return false;
        }
        if (!dayOfWeek) {
            alert(`Please select a day of week in row ${i + 1}.`);
            return false;
        }
        if (!dayOfSale) {
            alert(`Please enter a day of sale in row ${i + 1}.`);
            return false;
        }
        if (!productType) {
            alert(`Please select a product type in row ${i + 1}.`);
            return false;
        }
        if (!category) {
            alert(`Please select a category in row ${i + 1}.`);
            return false;
        }
        if (extraDetail === "") {
            alert(`Please choose an extra detail option in row ${i + 1}.`);
            return false;
        }
        // If the category is "SET", then ensure that a set type is selected.
        if (category === "SET") {
            let setType = row.querySelector('[name="set_type"]').value;
            if (!setType) {
                alert(`Please choose a set type for row ${i + 1}.`);
                return false;
            }
        }
        // (No validation required for the additional extra detail fields such as "other_detail", "zirconia_detail", etc.)
    }
    return true;
}

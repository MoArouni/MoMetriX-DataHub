function generateRows() {
    const numSales = parseInt(document.getElementById('num_sales').value);
    const rowsContainer = document.getElementById('sales-rows');
    rowsContainer.innerHTML = ""; // Clear existing rows

    for (let i = 0; i < numSales; i++) {
        const row = document.createElement('div');
        row.classList.add('row');
        row.innerHTML = `
            <label>Month:</label>
            <select name="month">
                <option value="Jan">January</option>
                <option value="Feb">February</option>
                <option value="Mar">March</option>
                <option value="Apr">April</option>
                <option value="May">May</option>
                <option value="Jun">June</option>
                <option value="Jul">July</option>
                <option value="Aug">August</option>
                <option value="Sep">September</option>
                <option value="Oct">October</option>
                <option value="Nov">November</option>
                <option value="Dec">December</option>
            </select>

            <label>Day of Week:</label>
            <select name="day_of_week">
                <option value="Mon">Monday</option>
                <option value="Tue">Tuesday</option>
                <option value="Wed">Wednesday</option>
                <option value="Thu">Thursday</option>
                <option value="Fri">Friday</option>
                <option value="Sat">Saturday</option>
                <option value="Sun">Sunday</option>
            </select>

            <label>Day of Sale:</label>
            <input type="date" name="day_of_sale" required>

            <label>Price:</label>
            <input type="number" name="price" step="0.01" required>

            <label>Card Amount Paid:</label>
            <input type="number" name="card_amount" step="0.01">

            <label>Cash Amount Paid:</label>
            <input type="number" name="cash_amount" step="0.01">

            <label>Product Type:</label>
            <select name="product_type" onchange="updateCategories(this, ${i})">
                <option value="" selected>Choose</option>
                {% for product_type in product_categories.keys() %}
                    <option value="{{ product_type }}">{{ product_type }}</option>
                {% endfor %}
            </select>

            <label>Category:</label>
            <select name="category" onchange="updateSetType(this, ${i})"></select>

            <label>Extra Detail:</label>
            <select name="extra_detail" onchange="updateExtraDetails(this, ${i})">
                <option value="" selected>Choose</option>
                <option value="mohave">Mohave Stone</option>
                <option value="zirconia">Zirconia</option>
                <option value="raw_stone">Raw Stone</option>
                <option value="other">Other</option>
            </select>

            <div id="other_detail_div_${i}" style="display: none;">
                <label>Other Detail:</label>
                <input type="text" name="other_detail">
            </div>

            <div id="zirconia_detail_div_${i}" style="display: none;">
                <label>Zirconia Options:</label>
                <select name="zirconia_detail">
                    <option value="Option1">Option1</option>
                    <option value="Option2">Option2</option>
                </select>
            </div>

            <div id="mohave_detail_div_${i}" style="display: none;">
                <label>Mohave Stone Options:</label>
                <select name="mohave_detail">
                    <option value="Option1">Option1</option>
                    <option value="Option2">Option2</option>
                </select>
            </div>

            <div id="raw_stone_detail_div_${i}" style="display: none;">
                <label>Raw Stone Options:</label>
                <select name="raw_stone_detail">
                    <option value="Option1">Option1</option>
                    <option value="Option2">Option2</option>
                </select>
            </div>

            <div id="set_type_div_${i}" style="display: none;">
                <label>Set Type:</label>
                <select name="set_type">
                    <option value="Necklace & Studs">Necklace & Studs</option>
                    <option value="Necklace & Earrings">Necklace & Earrings</option>
                    <option value="Necklace & Ring">Necklace & Ring</option>
                    <option value="Necklace & Bracelet">Necklace & Bracelet</option>
                    <option value="Necklace, Bracelet & Studs">Necklace, Bracelet & Studs</option>
                    <option value="Necklace, Bracelet & Ring">Necklace, Bracelet & Ring</option>
                    <option value="Necklace, Bracelet, Ring & Studs">Necklace, Bracelet, Ring & Studs</option>
                    <option value="Bracelet & Studs">Bracelet & Studs</option>
                    <option value="Bracelet & Ring">Bracelet & Ring</option>
                    <option value="Bracelet, Ring & Studs">Bracelet, Ring & Studs</option>
                    <option value="Ring & Studs">Ring & Studs</option>
                </select>
            </div>
        `;

        rowsContainer.appendChild(row);
    }
}

function updateCategories(select, index) {
    const productType = select.value;
    const categorySelect = document.getElementsByName('category')[index];
    categorySelect.innerHTML = "";

    const categories = JSON.parse('{{ product_categories|tojson }}')[productType] || [];
    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });
}

function updateSetType(select, index) {
    const setTypeDiv = document.getElementById(`set_type_div_${index}`);
    if (select.value === "SET") {
        setTypeDiv.style.display = "block";
    } else {
        setTypeDiv.style.display = "none";
    }
}

function updateExtraDetails(select, index) {
    const extraDetail = select.value;
    const otherDetailDiv = document.getElementById(`other_detail_div_${index}`);
    const zirconiaDiv = document.getElementById(`zirconia_detail_div_${index}`);
    const mohaveDiv = document.getElementById(`mohave_detail_div_${index}`);
    const rawStoneDiv = document.getElementById(`raw_stone_detail_div_${index}`);

    otherDetailDiv.style.display = "none";
    zirconiaDiv.style.display = "none";
    mohaveDiv.style.display = "none";
    rawStoneDiv.style.display = "none";

    if (extraDetail === "other") {
        otherDetailDiv.style.display = "block";
    } else if (extraDetail === "zirconia") {
        zirconiaDiv.style.display = "block";
    } else if (extraDetail === "mohave") {
        mohaveDiv.style.display = "block";
    } else if (extraDetail === "raw_stone") {
        rawStoneDiv.style.display = "block";
    }
}

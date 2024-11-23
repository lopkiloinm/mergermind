// Function to add a filter to the form
function addFilter(selectElement) {
    const selectedValue = selectElement.value;

    if (selectedValue) {
        // Check if the input already exists
        const existingFilterInputs = document.querySelectorAll('input[name="filter"]');
        let filterExists = false;

        existingFilterInputs.forEach(input => {
            if (input.value === selectedValue) {
                filterExists = true; // Filter already added
            }
        });

        // If the filter does not exist, add it as a hidden input field
        if (!filterExists) {
            let input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'filter';
            input.value = selectedValue;
            document.getElementById('filter-form').appendChild(input);
        }

        selectElement.value = ""; // Reset the select dropdown

        // Submit the form to apply filter
        document.getElementById('filter-form').submit();
    }
}

// Function to remove a specific filter
function removeFilter(category) {
    let formData = new FormData();
    const currentFilters = Array.from(new URLSearchParams(window.location.search).entries());
    currentFilters.forEach(([key, value]) => {
        if (key !== 'filter' || value !== category) {
            formData.append(key, value);
        }
    });
    // Update the URL to reflect the current filters
    const searchParams = new URLSearchParams(formData);
    window.location.search = searchParams.toString(); // Redirect to URL with remaining filters
}
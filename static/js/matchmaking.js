document.addEventListener('DOMContentLoaded', () => {
    removeEmptyInputsFromForm(); // Clean up any stray empty inputs on page load
});

function addFilter(selectElement) {
    // Get the selected category value from the dropdown
    const selectedValue = selectElement.value;
    
    // Only proceed if a valid (non-empty) category is selected
    if (selectedValue) {
        const existingFilterInputs = document.querySelectorAll('input[name="filter"]');
        let filterExists = false;

        // Check if the selected filter is already present in the form
        existingFilterInputs.forEach(input => {
            if (input.value === selectedValue) {
                filterExists = true;
            }
        });

        // If the filter doesn't exist, add it as a hidden input field
        if (!filterExists) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'filter';
            input.value = selectedValue;
            document.getElementById('filter-form').appendChild(input);
        }

        // Remove any inputs with empty values before submission
        removeEmptyInputsFromForm();
        
        // Reset dropdown to initial state (All)
        selectElement.value = "";

        // Submit the form
        document.getElementById('filter-form').submit();
    }
}

function sortByChanged(selectElement) {
    // Before submitting, ensure no empty filters are sent
    removeEmptyInputsFromForm();
    document.getElementById('filter-form').submit();
}

function removeFilter(category) {
    let formData = new FormData();
    const currentFilters = Array.from(new URLSearchParams(window.location.search).entries());

    currentFilters.forEach(([key, value]) => {
        if ((key !== 'filter' || value !== category) && value.trim()) {
            formData.append(key, value);
        }
    });

    const searchParams = new URLSearchParams(formData);
    window.location.search = searchParams.toString();
}

function removeEmptyInputsFromForm() {
    const existingInputs = document.querySelectorAll('input[name="filter"]');
    existingInputs.forEach(input => {
        if (!input.value.trim()) {
            input.parentNode.removeChild(input);
        }
    });
}
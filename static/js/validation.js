document.addEventListener('DOMContentLoaded', function() {
    // Add validation for all forms
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Special validation for donation forms
    const donationForms = document.querySelectorAll('.donation-form');
    
    donationForms.forEach(form => {
        const typeSelect = form.querySelector('select[name="type"]');
        const expiryDateField = form.querySelector('#expiry_date');
        const expiryDateGroup = expiryDateField ? expiryDateField.closest('.mb-3') : null;
        
        if (typeSelect && expiryDateGroup) {
            // Initial state based on selected value
            if (typeSelect.value === 'food') {
                expiryDateGroup.style.display = 'block';
                expiryDateField.setAttribute('required', '');
            } else {
                expiryDateGroup.style.display = 'none';
                expiryDateField.removeAttribute('required');
            }
            
            // Add event listener for changes
            typeSelect.addEventListener('change', function() {
                if (this.value === 'food') {
                    expiryDateGroup.style.display = 'block';
                    expiryDateField.setAttribute('required', '');
                } else {
                    expiryDateGroup.style.display = 'none';
                    expiryDateField.removeAttribute('required');
                    expiryDateField.value = '';
                }
            });
        }
    });
    
    // Validate expiry dates on food items
    const expiryDateFields = document.querySelectorAll('input[type="date"][name="expiry_date"]');
    
    expiryDateFields.forEach(field => {
        field.addEventListener('change', function() {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const selectedDate = new Date(this.value);
            
            if (selectedDate < today) {
                field.setCustomValidity('Expiry date cannot be in the past');
            } else {
                field.setCustomValidity('');
            }
        });
    });
});

// Function to validate numeric input
function validateNumericInput(input) {
    input.value = input.value.replace(/[^0-9]/g, '');
}

// Function to validate password match
function validatePasswordMatch(passwordField, confirmField, feedbackElement) {
    if (passwordField.value !== confirmField.value) {
        confirmField.setCustomValidity('Passwords do not match');
        feedbackElement.textContent = 'Passwords do not match';
    } else {
        confirmField.setCustomValidity('');
        feedbackElement.textContent = '';
    }
}

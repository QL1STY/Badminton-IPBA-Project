// Czekaj, aż cała strona się załaduje
document.addEventListener('DOMContentLoaded', function() {

    // --- Logika dla formularza rejestracji (walidacja na żywo) ---
    const registrationForm = document.getElementById('registration-form');
    
    if (registrationForm) {
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        const emailFeedback = document.getElementById('email-feedback');
        const passwordFeedback = document.getElementById('password-feedback');
        const submitButton = document.getElementById('submit-btn');

        function validateEmail() {
            if (!emailField || !emailFeedback) return true;
            const email = emailField.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; 

            if (emailRegex.test(email)) {
                emailFeedback.textContent = 'Poprawny format email.';
                emailFeedback.className = 'text-success form-text mt-1';
                return true;
            } else if (email === '') {
                emailFeedback.textContent = '';
                return false;
            } else {
                emailFeedback.textContent = 'Wprowadź poprawny adres email.';
                emailFeedback.className = 'text-danger form-text mt-1';
                return false;
            }
        }

        function validatePassword() {
            if (!passwordField || !passwordFeedback) return true;
            const password = passwordField.value;
            let errors = [];

            if (password.length < 4 || password.length > 24) errors.push('Hasło musi mieć od 4 do 24 znaków.');
            if (!/[a-z]/.test(password)) errors.push('Musi zawierać przynajmniej jedną małą literę.');
            if (!/[A-Z]/.test(password)) errors.push('Musi zawierać przynajmniej jedną dużą literę.');
            if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) errors.push('Musi zawierać przynajmniej jeden znak specjalny.');

            if (errors.length > 0) {
                passwordFeedback.innerHTML = errors.join('<br>');
                passwordFeedback.className = 'text-danger form-text mt-1';
                return false;
            } else if (password === '') {
                passwordFeedback.textContent = '';
                return false;
            } else {
                passwordFeedback.textContent = 'Hasło jest silne!';
                passwordFeedback.className = 'text-success form-text mt-1';
                return true;
            }
        }
        
        function validateForm() {
            const isEmailValid = validateEmail();
            const isPasswordValid = validatePassword();
            if (submitButton) {
                submitButton.disabled = !(isEmailValid && isPasswordValid);
            }
        }

        if (emailField) emailField.addEventListener('input', validateForm);
        if (passwordField) passwordField.addEventListener('input', validateForm);
        
        validateForm();
    }

    // --- Logika do pokazywania/ukrywania hasła (działa globalnie) ---
    const togglePassword = document.getElementById('togglePassword');
    const passwordField = document.getElementById('password');

    if (togglePassword && passwordField) {
        togglePassword.addEventListener('click', function() {
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            this.classList.toggle('fa-eye-slash');
        });
    }

    
});

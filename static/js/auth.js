// Authentication JavaScript for login and registration functionality
class AuthManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkExistingSession();
    }

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Registration form
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Password confirmation validation
        const confirmPassword = document.getElementById('confirmPassword');
        if (confirmPassword) {
            confirmPassword.addEventListener('input', () => this.validatePasswordMatch());
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        
        const email = formData.get('email');
        const password = formData.get('password');
        const remember = formData.get('remember');

        if (!this.validateLoginForm(email, password)) {
            return;
        }

        const button = form.querySelector('button[type="submit"]');
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="loading"></div> Signing in...';
        button.disabled = true;

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Store token
                if (remember) {
                    localStorage.setItem('auth_token', data.access_token);
                } else {
                    sessionStorage.setItem('auth_token', data.access_token);
                }

                this.showMessage('Login successful! Redirecting...', 'success');
                
                // Redirect immediately to dashboard
                window.location.href = '/';
            } else {
                this.showMessage(data.detail || 'Login failed. Please check your credentials.', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showMessage('An error occurred. Please try again.', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        // Collect form data
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password'),
            date_of_birth: formData.get('dateOfBirth'),
            current_stage: formData.get('currentStage'),
            study_level: formData.get('studyLevel'),
            topics_of_interest: this.getSelectedTopics(),
            current_goals: formData.get('currentGoals').split('\n').filter(goal => goal.trim()),
            preferred_learning_style: formData.get('preferredLearningStyle') || null
        };

        if (!this.validateRegistrationForm(userData)) {
            return;
        }

        const button = form.querySelector('button[type="submit"]');
        const originalText = button.innerHTML;
        button.innerHTML = '<div class="loading"></div> Creating account...';
        button.disabled = true;

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                // Store token
                localStorage.setItem('auth_token', data.access_token);
                localStorage.setItem('user_info', JSON.stringify(data.user));

                this.showMessage('Account created successfully! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                this.showMessage(data.detail || 'Registration failed. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showMessage('An error occurred. Please try again.', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    validateLoginForm(email, password) {
        if (!email || !password) {
            this.showMessage('Please fill in all required fields.', 'error');
            return false;
        }

        if (!this.isValidEmail(email)) {
            this.showMessage('Please enter a valid email address.', 'error');
            return false;
        }

        return true;
    }

    validateRegistrationForm(userData) {
        // Check required fields
        const requiredFields = ['username', 'email', 'password', 'date_of_birth', 'current_stage', 'study_level'];
        for (const field of requiredFields) {
            if (!userData[field]) {
                this.showMessage(`Please fill in the ${field.replace('_', ' ')} field.`, 'error');
                return false;
            }
        }

        // Validate email
        if (!this.isValidEmail(userData.email)) {
            this.showMessage('Please enter a valid email address.', 'error');
            return false;
        }

        // Validate password strength
        if (!this.isValidPassword(userData.password)) {
            this.showMessage('Password must be at least 8 characters long and contain letters and numbers.', 'error');
            return false;
        }

        // Validate username
        if (userData.username.length < 3) {
            this.showMessage('Username must be at least 3 characters long.', 'error');
            return false;
        }

        // Validate topics of interest
        if (userData.topics_of_interest.length === 0) {
            this.showMessage('Please select at least one topic of interest.', 'error');
            return false;
        }

        // Validate current goals
        if (userData.current_goals.length === 0 || userData.current_goals[0].trim() === '') {
            this.showMessage('Please enter at least one current goal.', 'error');
            return false;
        }

        return true;
    }

    validatePasswordMatch() {
        const password = document.getElementById('password');
        const confirmPassword = document.getElementById('confirmPassword');
        
        if (password && confirmPassword) {
            if (password.value !== confirmPassword.value) {
                confirmPassword.setCustomValidity('Passwords do not match');
            } else {
                confirmPassword.setCustomValidity('');
            }
        }
    }

    getSelectedTopics() {
        const checkboxes = document.querySelectorAll('input[name="topicsOfInterest"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    isValidPassword(password) {
        return password.length >= 8 && /[a-zA-Z]/.test(password) && /[0-9]/.test(password);
    }

    showMessage(message, type = 'info') {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.className = `${type}-message`;
            errorDiv.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        } else {
            alert(message);
        }
    }

    checkExistingSession() {
        const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
        if (token) {
            // Check if token is still valid
            this.validateToken(token).then(isValid => {
                if (isValid && window.location.pathname === '/login') {
                    window.location.href = '/';
                }
            });
        }
    }

    async validateToken(token) {
        try {
            const response = await fetch('/api/auth/validate', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Password toggle functionality
function togglePassword(fieldId = 'password') {
    const passwordField = document.getElementById(fieldId);
    const toggleButton = passwordField.nextElementSibling;
    const icon = toggleButton.querySelector('i');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        passwordField.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// Initialize authentication manager
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});

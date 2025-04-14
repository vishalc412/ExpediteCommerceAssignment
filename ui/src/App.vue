// App.vue
<template>
  <div class="app-container">
    <!-- Login Section (shown if not authenticated) -->
    <div v-if="!isAuthenticated" class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1>Expedite Commerce</h1>
          <h2>Customer Module</h2>
        </div>
        
        <div v-if="loginError" class="error-message">
          {{ loginError }}
        </div>
        
        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <label>Username</label>
            <div class="input-with-icon">
              <span class="field-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </span>
              <input 
                type="text" 
                v-model="username" 
                class="form-input" 
                placeholder="Enter username" 
                required
              />
            </div>
          </div>
          
          <div class="form-group">
            <label>Password</label>
            <div class="input-with-icon">
              <span class="field-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
              </span>
              <input 
                :type="showPassword ? 'text' : 'password'" 
                v-model="password" 
                class="form-input" 
                placeholder="Enter password" 
                required
              />
              <button 
                type="button" 
                @click="showPassword = !showPassword" 
                class="toggle-password"
              >
                <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
              </button>
            </div>
          </div>
          
          <button 
            type="submit" 
            class="login-button" 
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="loading-spinner"></span>
            {{ isLoading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Customer Search Section (shown if authenticated) -->
    <div v-else class="container">
      <div class="header-bar">
        <h1>Expedite Commerce Customer Module</h1>
        <div class="user-info">
          <span>{{ username }}</span>
          <button @click="logout" class="logout-button">Logout</button>
        </div>
      </div>
      
      <div class="search-card">
        <div class="tabs">
          <div class="tab active">Customer Search</div>
        </div>
        
        <div class="search-form">
          <div class="search-field">
            <label class="field-label">Customer Search</label>
            <div class="field-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
            </div>
            <input 
              type="text" 
              class="field-input" 
              v-model="searchQuery" 
              @keyup.enter="searchCustomers"
              placeholder="Enter customer name, location, etc."
            >
          </div>
          
          <div class="search-options">
            <button 
              class="search-button" 
              @click="searchCustomers"
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="loading-spinner"></span>
              {{ isLoading ? 'Searching...' : 'Search Customer Data' }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      
      <!-- Analysis Results Display -->
      <div v-if="hasSearched && !isLoading" class="results-container">
        <div class="analysis-header">
          <h2 class="results-header">
            Analysis Results <span v-if="analysisResults.items_found">({{ analysisResults.items_found }} items found)</span>
          </h2>
          <div class="analysis-meta" v-if="analysisResults.execution_time">
            <span class="execution-time">Execution time: {{ analysisResults.execution_time }}</span>
          </div>
        </div>
        
        <div class="analysis-card">
          <div class="analysis-content" v-html="formattedAnalysisResult"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

export default {
  name: 'App',
  setup() {
    // Authentication state
    const isAuthenticated = ref(false);
    const username = ref('');
    const password = ref('');
    const showPassword = ref(false);
    const loginError = ref('');
    const tokens = ref({
      idToken: '',
      accessToken: '',
      refreshToken: '',
      expiresIn: 0
    });

    // Search state
    const searchQuery = ref('');
    const isLoading = ref(false);
    const hasSearched = ref(false);
    const error = ref('');
    
    // Analysis results state
    const analysisResults = ref({
      result: '',
      items_found: 0,
      execution_time: ''
    });
    
    // API endpoints
    const LOGIN_API_URL = 'https://lger9st1a3.execute-api.us-east-2.amazonaws.com/test/login';
    const TOKEN_VALIDATOR_URL = 'https://a68p2cnnk2.execute-api.us-east-2.amazonaws.com/demo/validate-token';
    const CUSTOMER_DATA_API_URL = 'https://lger9st1a3.execute-api.us-east-2.amazonaws.com/test/getCustomerDetails';
    
    // Format analysis results for display with proper line breaks and formatting
    const formattedAnalysisResult = computed(() => {
      if (!analysisResults.value.result) return '';
      
      // Replace Unicode spaces with &nbsp; to preserve formatting
      // And convert newlines to <br> tags
      let formattedText = analysisResults.value.result
        .replace(/\u2003/g, '&nbsp;&nbsp;&nbsp;&nbsp;')
        .replace(/\n/g, '<br>')
        .replace(/•/g, '•&nbsp;');
      
      return formattedText;
    });
    
    // Check authentication status on mount
    onMounted(() => {
      checkAuth();
    });
    
    // Check if user is already authenticated
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('access_token');
      const storedUsername = localStorage.getItem('username');
      
      if (storedToken) {
        // Check if token is still valid
        try {
          console.log('Validating token...');
          const response = await axios.get(TOKEN_VALIDATOR_URL, {
            headers: {
              'Authorization': `Bearer ${storedToken}`
            }
          });
          
          // If validation successful
          if (response.data.success) {
            tokens.value.accessToken = storedToken;
            // Use username from token validation if available
            username.value = response.data.user?.username || storedUsername;
            isAuthenticated.value = true;
            console.log("Token validated successfully");
          } else {
            // Token invalid, clear storage and redirect to login
            console.log("Token validation failed");
            logout();
          }
        } catch (error) {
          console.error("Token validation error:", error);
          // On validation error, clear storage and redirect to login
          if (storedUsername) {
            // If we can't validate but have a username, still allow access
            // This is a fallback for local development or when token validation is unavailable
            tokens.value.accessToken = storedToken;
            username.value = storedUsername;
            isAuthenticated.value = true;
            console.log("Using cached credentials");
          } else {
            logout();
          }
        }
      }
    };
    
    // Login function
    const login = async () => {
      if (!username.value || !password.value) {
        loginError.value = 'Please enter both username and password';
        return;
      }
      
      loginError.value = '';
      isLoading.value = true;
      
      try {
        console.log('Attempting login...');
        
        const response = await axios.post(LOGIN_API_URL, {
          username: username.value,
          password: password.value
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('Login response:', response.data);
        
        // Store tokens
        tokens.value = {
          idToken: response.data.id_token,
          accessToken: response.data.access_token,
          refreshToken: response.data.refresh_token,
          expiresIn: response.data.expires_in
        };
        
        // Store in localStorage
        localStorage.setItem('id_token', response.data.id_token);
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('refresh_token', response.data.refresh_token);
        localStorage.setItem('token_expiry', Date.now() + (response.data.expires_in * 1000));
        localStorage.setItem('username', username.value);
        
        // Update authentication state
        isAuthenticated.value = true;
      } catch (err) {
        console.error('Login error:', err);
        
        if (!err.response) {
          loginError.value = 'Unable to connect to the server. Please try again.';
        } else if (err.response.status === 401) {
          loginError.value = 'Invalid username or password';
        } else {
          loginError.value = err.response?.data?.error || 'An error occurred during login';
        }
        
        password.value = ''; // Clear password field on error
      } finally {
        isLoading.value = false;
      }
    };
    
    // Logout function
    const logout = () => {
      // Clear tokens
      tokens.value = {
        idToken: '',
        accessToken: '',
        refreshToken: '',
        expiresIn: 0
      };
      
      // Clear localStorage
      localStorage.removeItem('id_token');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('token_expiry');
      localStorage.removeItem('username');
      
      // Reset state
      isAuthenticated.value = false;
      username.value = '';
      password.value = '';
      searchQuery.value = '';
      hasSearched.value = false;
      analysisResults.value = {
        result: '',
        items_found: 0,
        execution_time: ''
      };
    };
    
    // Format date for display
    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleDateString();
    };

// Modified searchCustomers function that might bypass CORS issues
const searchCustomers = async () => {
  if (!searchQuery.value.trim()) {
    error.value = 'Please enter a search query';
    return;
  }
  
  error.value = '';
  isLoading.value = true;
  hasSearched.value = true;
  
  try {
    const searchTerm = searchQuery.value.trim();
    console.log('Starting customer data search for:', searchTerm);
    
    // 1. Include the API key in the request payload instead of as a header
    const requestPayload = {
      table_name: "CustomerData",
      prompt: "Analyze this data and tell me the key trends.",
      search_query: searchTerm,
      api_key: "yourapikey"
    };
    
    // 2. Use XMLHttpRequest instead of fetch to have more control
    // This is more old-school but sometimes helps with CORS issues
    const xhr = new XMLHttpRequest();
    xhr.open('POST', CUSTOMER_DATA_API_URL, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    // 3. Use the access token from your authentication
    if (tokens.value.accessToken) {
      xhr.setRequestHeader('Authorization', `Bearer ${tokens.value.accessToken}`);
    }
    
    // 4. Handle the response with promise
    const responsePromise = new Promise((resolve, reject) => {
      xhr.onload = function() {
        if (this.status >= 200 && this.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            reject(new Error('Invalid JSON response'));
          }
        } else {
          reject(new Error(`HTTP error ${this.status}: ${xhr.statusText}`));
        }
      };
      
      xhr.onerror = function() {
        reject(new Error('Network error occurred'));
      };
    });
    
    // 5. Send the request
    xhr.send(JSON.stringify(requestPayload));
    
    // 6. Await the response
    const responseData = await responsePromise;
    console.log('API response:', responseData);
    
    // 7. Store results
    analysisResults.value = responseData;
    
  } catch (err) {
    console.error('Error searching customers:', err);
    error.value = err.message || 'An error occurred while searching. Please try again.';
    
    analysisResults.value = {
      result: '',
      items_found: 0,
      execution_time: ''
    };
  } finally {
    isLoading.value = false;
  }
};

    return {
      // Authentication
      isAuthenticated,
      username,
      password,
      showPassword,
      loginError,
      login,
      logout,
      
      // Search
      searchQuery,
      isLoading,
      hasSearched,
      error,
      searchCustomers,
      formatDate,
      
      // Analysis
      analysisResults,
      formattedAnalysisResult
    };
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

body {
  background-color: #eef1f8;
  color: #333;
  min-height: 100vh;
}

.app-container {
  width: 100%;
  min-height: 100vh;
}

/* Login Styles */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #eef1f8;
}

.login-card {
  width: 100%;
  max-width: 450px;
  background-color: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #111;
}

.login-header h2 {
  font-size: 18px;
  font-weight: 500;
  color: #666;
}

.login-form {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 15px;
  color: #333;
}

.input-with-icon {
  position: relative;
}

.field-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  color: #666;
  z-index: 1;
}

.form-input {
  width: 100%;
  padding: 12px 12px 12px 44px;
  font-size: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  height: 52px;
  background-color: white;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #999;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.05);
}

.form-input::placeholder {
  color: #aaa;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  width: 24px;
  height: 24px;
  padding: 0;
  z-index: 1;
}

.login-button {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  background-color: #111;
  color: white;
  font-weight: 600;
  font-size: 16px;
  padding: 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-button:hover {
  background-color: #333;
}

.login-button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

/* Header Bar */
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background-color: white;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.header-bar h1 {
  font-size: 22px;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info span {
  font-weight: 500;
}

.logout-button {
  background-color: #f0f0f0;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-button:hover {
  background-color: #e0e0e0;
}

/* Customer Search Styles */
.container {
  max-width: 1024px;
  margin: 40px auto;
  padding: 0 20px;
}

.search-card {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #f0f0f0;
}

.tab {
  padding: 24px 20px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  border-bottom: 3px solid #333;
  margin-bottom: -1px;
}

.search-form {
  padding: 32px;
}

.search-field {
  position: relative;
  margin-bottom: 30px;
}

.field-label {
  display: block;
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 16px;
  color: #333;
}

.field-input {
  width: 100%;
  padding: 12px 12px 12px 44px;
  font-size: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  height: 56px;
  background-color: white;
  transition: all 0.3s ease;
}

.field-input:focus {
  outline: none;
  border-color: #999;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.05);
}

.field-input::placeholder {
  color: #aaa;
}

.search-options {
  display: flex;
  justify-content: flex-end;
}

.search-button {
  background-color: #111;
  color: white;
  font-weight: 600;
  font-size: 16px;
  padding: 16px 32px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
}

.search-button:hover {
  background-color: #333;
}

.search-button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.results-container {
  margin-top: 30px;
}

.results-header {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  background-color: #fff0f0;
  color: #d00000;
  padding: 12px;
  border-radius: 8px;
  margin-top: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.empty-results {
  text-align: center;
  padding: 40px 0;
  color: #888;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #ccc;
}

/* Analysis results styles */
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.analysis-meta {
  font-size: 14px;
  color: #666;
}

.execution-time {
  background-color: #f5f5f5;
  padding: 6px 12px;
  border-radius: 16px;
  font-weight: 500;
}

.analysis-card {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.analysis-content {
  line-height: 1.6;
  color: #333;
}

.analysis-content ul, .analysis-content ol {
  margin-left: 24px;
  margin-bottom: 16px;
}

.analysis-content p {
  margin-bottom: 16px;
}

.analysis-content br {
  display: block;
  margin: 8px 0;
}

@media (max-width: 768px) {
  .customer-details {
    grid-template-columns: 1fr;
  }
  
  .header-bar {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .user-info {
    width: 100%;
    justify-content: space-between;
  }
  
  .analysis-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .search-button, .login-button {
    width: 100%;
  }
  
  .login-card, .search-form {
    padding: 24px 16px;
  }
}
</style>
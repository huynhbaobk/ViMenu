/**
 * Configuration constants for the application
 */

const CONFIG = {
    API: {
        BASE_URL: window.location.origin + '/api/v1',
        TIMEOUT: 30000,
        RETRY_ATTEMPTS: 3,
        RETRY_DELAY: 1000
    },
    
    UI: {
        DISHES_PER_PAGE: 9,
        RATE_LIMIT_DELAY: 20000, // 20 seconds for 3 RPM
        DEBOUNCE_DELAY: 300,
        ANIMATION_DURATION: 250
    },
    
    FILE: {
        MAX_SIZE: 5 * 1024 * 1024, // 5MB
        ALLOWED_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'],
        SUPPORTED_FORMATS: '.jpg, .jpeg, .png, .webp'
    },
    
    POLLING: {
        INITIAL_DELAY: 2000,
        MAX_ATTEMPTS: 30,
        BACKOFF_MULTIPLIER: 1.2
    }
};

// Freeze configuration to prevent modifications
Object.freeze(CONFIG);
Object.freeze(CONFIG.API);
Object.freeze(CONFIG.UI);
Object.freeze(CONFIG.FILE);
Object.freeze(CONFIG.POLLING);

export default CONFIG;

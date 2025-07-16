/**
 * API service for communicating with the backend
 */

const API_BASE_URL = window.location.origin + '/api/v1';

class ApiService {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    async analyzeMenu(file, includeRecipes = true) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('include_recipes', includeRecipes);

        try {
            const response = await fetch(`${this.baseUrl}/analyze-menu`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze menu');
            }

            return await response.json();
        } catch (error) {
            console.error('Error analyzing menu:', error);
            throw error;
        }
    }

    async getAnalysisStatus(requestId) {
        try {
            const response = await fetch(`${this.baseUrl}/analysis/${requestId}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get analysis status');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting analysis status:', error);
            throw error;
        }
    }

    async getRecipe(requestId, dishName) {
        try {
            const response = await fetch(`${this.baseUrl}/recipes/${requestId}/${encodeURIComponent(dishName)}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get recipe');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting recipe:', error);
            throw error;
        }
    }

    async getIngredients(requestId, dishName) {
        try {
            const response = await fetch(`${this.baseUrl}/ingredients/${requestId}/${encodeURIComponent(dishName)}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get ingredients');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting ingredients:', error);
            throw error;
        }
    }

    async getBatchIngredients(requestId, dishNames) {
        try {
            const response = await fetch(`${this.baseUrl}/ingredients/batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    request_id: requestId,
                    dish_names: dishNames
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get batch ingredients');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting batch ingredients:', error);
            throw error;
        }
    }

    async pollAnalysisStatus(requestId, callback, interval = 2000) {
        const poll = async () => {
            try {
                const result = await this.getAnalysisStatus(requestId);
                callback(result);
                
                if (result.status === 'processing') {
                    setTimeout(poll, interval);
                }
            } catch (error) {
                console.error('Error polling status:', error);
                callback({ status: 'error', message: error.message });
            }
        };

        poll();
    }
}

// Export for use in other modules
window.apiService = new ApiService();
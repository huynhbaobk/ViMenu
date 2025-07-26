/**
 * Main application logic
 */

class MenuApp {
    constructor() {
        this.currentRequestId = null;
        this.analysisResult = null;
        this.displayedDishes = 0;
        this.dishesPerPage = 9;
        this.lastApiCallTime = 0;
        this.rateLimitDelay = 20000; // 20 seconds between calls for 3 RPM
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        const fileInput = document.getElementById('fileInput');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const changeImageBtn = document.getElementById('changeImageBtn');

        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        analyzeBtn.addEventListener('click', () => this.analyzeCurrentImage());
        changeImageBtn.addEventListener('click', () => this.resetUpload());

        // Prevent default drag behavior
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }

    setupDragAndDrop() {
        const uploadZone = document.getElementById('uploadZone');

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });

        uploadZone.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Vui lòng chọn file ảnh!');
            return;
        }

        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            alert('File quá lớn! Kích thước tối đa 5MB.');
            return;
        }

        this.previewFile(file);
    }

    previewFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewImage = document.getElementById('previewImage');
            previewImage.src = e.target.result;
            
            document.getElementById('uploadZone').style.display = 'none';
            document.getElementById('previewSection').style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Store file for later use
        this.currentFile = file;
    }

    async analyzeCurrentImage() {
        if (!this.currentFile) return;

        // Rate limiting check
        const now = Date.now();
        const timeSinceLastCall = now - this.lastApiCallTime;
        
        if (timeSinceLastCall < this.rateLimitDelay) {
            const waitTime = Math.ceil((this.rateLimitDelay - timeSinceLastCall) / 1000);
            alert(`Vui lòng đợi ${waitTime} giây trước khi gửi yêu cầu tiếp theo.`);
            return;
        }

        this.showLoading();
        
        try {
            this.lastApiCallTime = now;
            const result = await window.apiService.analyzeMenu(this.currentFile, true);
            this.currentRequestId = result.request_id;
            this.analysisResult = result;
            this.displayedDishes = 0;
            
            this.displayResults(result);
            
            // Start polling for updates if still processing
            if (result.status === 'processing') {
                this.startPolling();
            }
            
        } catch (error) {
            console.error('Error analyzing menu:', error);
            alert('Có lỗi xảy ra khi phân tích menu: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        document.getElementById('previewSection').style.display = 'none';
        document.getElementById('uploadLoading').style.display = 'block';
    }

    hideLoading() {
        document.getElementById('uploadLoading').style.display = 'none';
        document.getElementById('previewSection').style.display = 'block';
    }

    displayResults(result) {
        const content = document.getElementById('resultsContent');
        const statusIndicator = document.getElementById('statusIndicator');

        // Update status
        statusIndicator.textContent = this.getStatusText(result.status);
        statusIndicator.className = `status-indicator ${result.status}`;

        if (result.dishes.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h3>Không tìm thấy món ăn</h3>
                    <p>${result.message || 'Vui lòng thử ảnh khác'}</p>
                </div>
            `;
            return;
        }

        this.renderDishGrid(result.dishes);
    }

    renderDishGrid(dishes) {
        const content = document.getElementById('resultsContent');
        const dishGrid = document.createElement('div');
        dishGrid.className = 'dish-grid';
        dishGrid.id = 'dishGrid';

        // Display initial dishes (first 9)
        const initialDishes = dishes.slice(0, this.dishesPerPage);
        this.displayedDishes = initialDishes.length;

        initialDishes.forEach((dish, index) => {
            const dishCard = this.createDishCard(dish, index);
            dishGrid.appendChild(dishCard);
        });

        content.innerHTML = '';
        content.appendChild(dishGrid);

        // Add load more button if there are more dishes
        if (dishes.length > this.dishesPerPage) {
            const loadMoreBtn = this.createLoadMoreButton();
            content.appendChild(loadMoreBtn);
        }

        // Start fetching ingredients for visible dishes
        this.loadIngredientsForVisibleDishes();
    }

    createDishCard(dish, index) {
        const card = document.createElement('div');
        card.className = 'dish-card';
        card.setAttribute('data-dish-index', index);

        const priceDisplay = dish.price ? `<span class="dish-price">${dish.price}</span>` : '';
        const imageDisplay = dish.image_url 
            ? `<img src="${dish.image_url}" alt="${dish.name}" class="dish-image">`
            : `<div class="dish-image-placeholder">🍜</div>`;

        card.innerHTML = `
            <div class="dish-image-container">
                ${imageDisplay}
            </div>
            <div class="dish-content">
                <div class="dish-header">
                    <div class="dish-name">${dish.name}</div>
                    ${priceDisplay}
                </div>
                <div class="dish-ingredients" id="ingredients-${index}">
                    <div class="ingredients-loading">Đang tải nguyên liệu...</div>
                </div>
            </div>
        `;

        // Đã bỏ sự kiện click mở popup công thức
        
        return card;
    }

    createLoadMoreButton() {
        const button = document.createElement('button');
        button.className = 'load-more-btn';
        button.textContent = 'Xem thêm món ăn';
        button.onclick = (e) => {
            e.preventDefault(); 
            this.loadMoreDishes();
        };
        return button;
    }

    async loadMoreDishes() {
        console.log("Loading more dishes...");
        
        // Kiểm tra kết quả phân tích có tồn tại không
        if (!this.analysisResult || !this.analysisResult.dishes) {
            console.error("Không có kết quả phân tích hoặc món ăn");
            return;
        }
        
        // Kiểm tra nếu đã hiển thị tất cả các món
        if (this.displayedDishes >= this.analysisResult.dishes.length) {
            console.log("Đã hiển thị tất cả món ăn");
            return;
        }

        // Tính toán chỉ số bắt đầu và kết thúc cho các món mới
        const startIndex = this.displayedDishes;
        const endIndex = Math.min(startIndex + this.dishesPerPage, this.analysisResult.dishes.length);
        const newDishes = this.analysisResult.dishes.slice(startIndex, endIndex);
        console.log(`Đang tải món từ ${startIndex} đến ${endIndex}:`, newDishes);

        // Tìm grid hiển thị các món
        const dishGrid = document.getElementById('dishGrid');
        if (!dishGrid) {
            console.error("Không tìm thấy dish grid");
            return;
        }

        // Hiển thị trạng thái "đang tải" thay cho nút Xem thêm
        const loadMoreBtn = document.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.textContent = 'Đang tải...';
            loadMoreBtn.disabled = true;
        }
        
        // Thêm món mới vào grid
        try {
            newDishes.forEach((dish, relativeIndex) => {
                const actualIndex = startIndex + relativeIndex;
                console.log(`Tạo card cho món ${dish.name} tại vị trí ${actualIndex}`);
                const dishCard = this.createDishCard(dish, actualIndex);
                dishGrid.appendChild(dishCard);
            });

            // Cập nhật số món đã hiển thị
            this.displayedDishes = endIndex;
            console.log("Đã cập nhật số món hiển thị:", this.displayedDishes);

            // Tải nguyên liệu cho các món mới thêm vào
            await this.loadIngredientsForNewDishes(startIndex, endIndex);
            
            // Ẩn nút "Xem thêm" nếu đã hiển thị tất cả món
            if (this.displayedDishes >= this.analysisResult.dishes.length) {
                console.log("Không còn món nào để tải, đã xóa nút");
                if (loadMoreBtn) loadMoreBtn.remove();
            } else {
                // Khôi phục nút Xem thêm nếu còn món
                if (loadMoreBtn) {
                    loadMoreBtn.textContent = 'Xem thêm món ăn';
                    loadMoreBtn.disabled = false;
                }
            }
        } catch (error) {
            console.error("Lỗi khi tải thêm món:", error);
            // Khôi phục nút nếu có lỗi
            if (loadMoreBtn) {
                loadMoreBtn.textContent = 'Xem thêm món ăn';
                loadMoreBtn.disabled = false;
            }
        }
    }

    async loadIngredientsForVisibleDishes() {
        const visibleDishes = this.analysisResult.dishes.slice(0, this.dishesPerPage);
        const dishNames = visibleDishes.map(dish => dish.name);

        try {
            const response = await window.apiService.getBatchIngredients(this.currentRequestId, dishNames);
            
            response.results.forEach((result, index) => {
                this.updateDishIngredients(index, result.ingredients);
            });
        } catch (error) {
            console.error('Error loading batch ingredients:', error);
            // Fallback to individual loading
            visibleDishes.forEach((dish, index) => {
                this.loadSingleDishIngredients(dish.name, index);
            });
        }
    }

    async loadIngredientsForNewDishes(startIndex, endIndex) {
        console.log(`Loading ingredients for dishes from index ${startIndex} to ${endIndex}`);
        const newDishes = this.analysisResult.dishes.slice(startIndex, endIndex);
        
        // Try batch loading first
        try {
            const dishNames = newDishes.map(dish => dish.name);
            console.log("Loading ingredients for dishes:", dishNames);
            
            const response = await window.apiService.getBatchIngredients(this.currentRequestId, dishNames);
            
            response.results.forEach((result, i) => {
                const actualIndex = startIndex + i;
                console.log(`Updating ingredients for ${result.dish_name} at index ${actualIndex}`);
                this.updateDishIngredients(actualIndex, result.ingredients);
            });
        } catch (error) {
            console.error("Error loading batch ingredients for new dishes:", error);
            
            // Fallback to individual loading
            newDishes.forEach((dish, relativeIndex) => {
                const actualIndex = startIndex + relativeIndex;
                console.log(`Fallback: Loading ingredients for ${dish.name} at index ${actualIndex}`);
                this.loadSingleDishIngredients(dish.name, actualIndex);
            });
        }
    }

    async loadSingleDishIngredients(dishName, index) {
        try {
            const response = await window.apiService.getIngredients(this.currentRequestId, dishName);
            this.updateDishIngredients(index, response.ingredients);
        } catch (error) {
            console.error(`Error loading ingredients for ${dishName}:`, error);
            this.updateDishIngredients(index, [], true);
        }
    }

    updateDishIngredients(index, ingredients, isError = false) {
        const container = document.getElementById(`ingredients-${index}`);
        if (!container) return;

        console.log("Ingredients at index", index, ":", ingredients);

        if (isError) {
            container.innerHTML = '<div class="ingredients-empty"> Đang Đang  Đang chuẩn bị nguyên liệu...</div>';
            return;
        }

        if (!ingredients || ingredients.length === 0) {
            container.innerHTML = '<div class="ingredients-empty">Nguyên liệu đang được cập nhật</div>';
            return;
        }

        let ingredientsText = '';

        if (typeof ingredients === 'string') {
            // Trường hợp chuỗi văn bản đơn giản
            ingredientsText = ingredients;
        } else if (Array.isArray(ingredients)) {
            // Trường hợp danh sách object như cũ
            ingredientsText = ingredients.map(ing => ing.item || '').filter(Boolean).join(', ');
        }

        console.log("Formatted ingredients text:", ingredientsText);

        container.innerHTML = `
            <div class="ingredients-list">
                <div class="ingredient-item-text">
                    ${ingredientsText}
                </div>
            </div>
        `;

    }


    startPolling() {
        if (!this.currentRequestId) {
            console.error("Không có request ID để poll");
            return;
        }
        
        console.log("Bắt đầu polling với request ID:", this.currentRequestId);
        
        // Lấy kết quả phân tích hiện tại
        window.apiService.getAnalysisStatus(this.currentRequestId)
            .then(result => {
                console.log("Kết quả polling:", result);
                if (result && result.dishes) {
                    console.log("Cập nhật kết quả phân tích với", result.dishes.length, "món");
                    this.analysisResult = result;
                    this.displayResults(result);
                }
            })
            .catch(error => {
                console.error("Lỗi khi polling:", error);
            });
    }

    resetUpload() {
        document.getElementById('uploadZone').style.display = 'flex';
        document.getElementById('previewSection').style.display = 'none';
        document.getElementById('fileInput').value = '';
        this.currentFile = null;
        this.displayedDishes = 0;
        
        // Reset results
        const content = document.getElementById('resultsContent');
        content.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🍜</div>
                <h3>Chưa có món ăn</h3>
                <p>Tải ảnh menu bên phải để bắt đầu khám phá</p>
            </div>
        `;
        
        const statusIndicator = document.getElementById('statusIndicator');
        statusIndicator.textContent = 'Chưa có dữ liệu';
        statusIndicator.className = 'status-indicator';
    }

    getStatusText(status) {
        const statusMap = {
            'processing': 'Đang xử lý...',
            'completed': 'Hoàn thành',
            'error': 'Có lỗi',
            'no_dishes_found': 'Không tìm thấy món ăn'
        };
        return statusMap[status] || status;
    }
}


// Initialize app when DOM is ready
// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.menuApp = new MenuApp();
});
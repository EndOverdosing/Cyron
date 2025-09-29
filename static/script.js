document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const numImagesSelect = document.getElementById('num-images-select');
    const submitButton = document.getElementById('submit-button');
    const outputArea = document.getElementById('output-area');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    const themeSwitcher = document.getElementById('theme-switcher');

    const savePreference = (key, value) => localStorage.setItem(key, value);
    const getPreference = (key) => localStorage.getItem(key);

    function applySavedPreferences() {
        const savedTheme = getPreference('theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-theme');
        }
        const savedNumImages = getPreference('num_images');
        if (savedNumImages) {
            numImagesSelect.value = savedNumImages;
        }
    }

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const newTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        savePreference('theme', newTheme);
    });

    numImagesSelect.addEventListener('change', () => savePreference('num_images', numImagesSelect.value));

    function handleMouseMove(e) {
        document.body.style.setProperty('--cursor-x', `${e.clientX}px`);
        document.body.style.setProperty('--cursor-y', `${e.clientY}px`);
        document.body.style.setProperty('--cursor-opacity', '1');
    }

    function handleMouseLeave() {
        document.body.style.setProperty('--cursor-opacity', '0');
    }

    function addInteractiveBorderListeners(element) {
        element.addEventListener('mousemove', e => {
            const rect = element.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            element.style.setProperty('--x', `${x}px`);
            element.style.setProperty('--y', `${y}px`);
            element.style.setProperty('--opacity', '1');
        });
        element.addEventListener('mouseleave', () => {
            element.style.setProperty('--opacity', '0');
        });
    }

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.querySelectorAll('.interactive-border').forEach(addInteractiveBorderListeners);

    async function startSearch(event) {
        event.preventDefault();
        const query = queryInput.value.trim();
        if (!query) {
            showError("Please enter a search query.");
            return;
        }

        submitButton.disabled = true;
        outputArea.innerHTML = '';
        progressContainer.classList.remove('hidden');
        updateProgress(10, "Initializing search...");

        try {
            updateProgress(30, "Finding images...");
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    num_images: numImagesSelect.value,
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || `Server error: ${response.statusText}`);
            }

            updateProgress(100, "Displaying results...");
            displayImages(data.images);
            setTimeout(() => {
                progressContainer.classList.add('hidden');
            }, 500);

        } catch (e) {
            console.error("Error:", e);
            showError(e.message);
            progressContainer.classList.add('hidden');
        } finally {
            submitButton.disabled = false;
        }
    }

    window.startSearch = startSearch;

    function displayImages(imageUrls) {
        outputArea.innerHTML = '';
        const grid = document.createElement('div');
        grid.id = 'image-results-grid';

        imageUrls.forEach((url, index) => {
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'image-result';
            link.style.animationDelay = `${index * 50}ms`;

            const img = document.createElement('img');
            img.src = url;
            img.alt = `Search result ${index + 1}`;
            img.loading = 'lazy';

            link.appendChild(img);
            grid.appendChild(link);
        });

        outputArea.appendChild(grid);
    }

    function updateProgress(percentage, status) {
        progressBar.style.width = `${percentage}%`;
        progressStatus.textContent = status;
    }

    function showError(message) {
        outputArea.innerHTML = `<div class="error-box">${message}</div>`;
    }

    applySavedPreferences();
});
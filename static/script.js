document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const imageSizeSelect = document.getElementById('image-size-select');
    const timeRangeSelect = document.getElementById('time-range-select');
    const safeSearchToggle = document.getElementById('safe-search-toggle');
    const submitButton = document.getElementById('submit-button');
    const outputArea = document.getElementById('output-area');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressStatus = document.getElementById('progress-status');
    const themeSwitcher = document.getElementById('theme-switcher');
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = lightbox.querySelector('.lightbox-image');

    let currentQuery = '';
    let currentPage = 1;
    let isLoading = false;
    let noMoreResults = false;
    let allImageUrls = [];
    let currentLightboxIndex = -1;

    const savePreference = (key, value) => localStorage.setItem(key, value);
    const getPreference = (key) => localStorage.getItem(key);

    function applySavedPreferences() {
        const savedTheme = getPreference('theme');
        if (savedTheme === 'light') document.body.classList.add('light-theme');

        const savedSize = getPreference('image_size');
        if (savedSize) imageSizeSelect.value = savedSize;

        const savedTime = getPreference('time_range');
        if (savedTime) timeRangeSelect.value = savedTime;

        const savedSafeSearch = getPreference('safe_search');
        if (savedSafeSearch === 'false') safeSearchToggle.checked = false;
    }

    themeSwitcher.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const newTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        savePreference('theme', newTheme);
    });

    imageSizeSelect.addEventListener('change', () => savePreference('image_size', imageSizeSelect.value));
    timeRangeSelect.addEventListener('change', () => savePreference('time_range', timeRangeSelect.value));
    safeSearchToggle.addEventListener('change', () => savePreference('safe_search', safeSearchToggle.checked));

    function handleMouseMove(e) {
        document.body.style.setProperty('--cursor-x', `${e.clientX}px`);
        document.body.style.setProperty('--cursor-y', `${e.clientY}px`);
        document.body.style.setProperty('--cursor-opacity', '1');
    }

    function handleMouseLeave() { document.body.style.setProperty('--cursor-opacity', '0'); }

    function addInteractiveBorderListeners(element) {
        element.addEventListener('mousemove', e => {
            const rect = element.getBoundingClientRect();
            element.style.setProperty('--x', `${e.clientX - rect.left}px`);
            element.style.setProperty('--y', `${e.clientY - rect.top}px`);
            element.style.setProperty('--opacity', '1');
        });
        element.addEventListener('mouseleave', () => element.style.setProperty('--opacity', '0'));
    }

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.querySelectorAll('.interactive-border').forEach(addInteractiveBorderListeners);

    async function startSearch(query) {
        if (!query) {
            showError("Please enter a search query.");
            return;
        }

        document.body.classList.add('search-active');
        currentQuery = query;
        currentPage = 1;
        allImageUrls = [];
        noMoreResults = false;
        outputArea.innerHTML = '';
        progressContainer.classList.remove('hidden');
        updateProgress(10, "Initializing search...");

        const url = new URL(window.location);
        url.pathname = '/search';
        url.searchParams.set('query', query);
        window.history.pushState({ query }, '', url);

        await fetchAndDisplayImages(true);

        setTimeout(() => progressContainer.classList.add('hidden'), 500);
    }

    window.handleFormSubmit = function (event) {
        event.preventDefault();
        const query = queryInput.value.trim();
        startSearch(query);
    }

    async function fetchAndDisplayImages(isNewSearch = false) {
        if (isLoading || noMoreResults) return;

        isLoading = true;
        submitButton.disabled = true;
        const loadMoreButton = document.getElementById('load-more-button');
        if (loadMoreButton) {
            loadMoreButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            loadMoreButton.disabled = true;
        }

        try {
            if (isNewSearch) updateProgress(30, "Finding images...");

            const response = await fetch('/search_api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: currentQuery,
                    safe_search: safeSearchToggle.checked,
                    size: imageSizeSelect.value,
                    time_range: timeRangeSelect.value,
                    page: currentPage
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                noMoreResults = true;
                if (loadMoreButton) loadMoreButton.remove();
                if (isNewSearch) showError(data.error || "No images found.");
                return;
            }

            if (!data.images || data.images.length === 0) {
                noMoreResults = true;
                if (loadMoreButton) loadMoreButton.remove();
                if (isNewSearch) showError("No more images found for this query.");
                return;
            }

            if (isNewSearch) updateProgress(100, "Displaying results...");

            const newImageUrls = data.images.filter(url => !allImageUrls.includes(url));
            allImageUrls.push(...newImageUrls);
            displayImages(newImageUrls);
            currentPage++;

        } catch (e) {
            console.error("Error:", e);
            showError("A network error occurred or the server response was invalid. Please try again.");
        } finally {
            isLoading = false;
            submitButton.disabled = false;
            const finalLoadMoreButton = document.getElementById('load-more-button');
            if (finalLoadMoreButton) {
                finalLoadMoreButton.innerHTML = 'Load More';
                finalLoadMoreButton.disabled = false;
            }
        }
    }

    function displayImages(imageUrls) {
        let grid = document.getElementById('image-results-grid');
        if (!grid) {
            grid = document.createElement('div');
            grid.id = 'image-results-grid';
            outputArea.appendChild(grid);
        }

        imageUrls.forEach(url => {
            const startIndex = allImageUrls.length - imageUrls.length;
            const link = document.createElement('a');
            link.href = url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.className = 'image-result';
            link.style.animationDelay = `${(grid.children.length % 20) * 50}ms`;
            link.dataset.index = startIndex + grid.children.length;

            link.addEventListener('click', e => {
                e.preventDefault();
                openLightbox(parseInt(link.dataset.index));
            });

            const img = document.createElement('img');
            img.src = url;
            img.alt = `${currentQuery} result`;
            img.loading = 'lazy';

            img.onerror = () => {
                link.remove();
            };

            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.innerHTML = `<button class="copy-url-btn" title="Copy URL"><i class="fa-solid fa-copy"></i></button>`;
            overlay.querySelector('.copy-url-btn').addEventListener('click', e => {
                e.stopPropagation();
                e.preventDefault();
                copyUrlToClipboard(url, e.currentTarget);
            });

            link.appendChild(img);
            link.appendChild(overlay);
            grid.appendChild(link);
        });

        let loadMoreButton = document.getElementById('load-more-button');
        if (!loadMoreButton && !noMoreResults) {
            loadMoreButton = document.createElement('button');
            loadMoreButton.id = 'load-more-button';
            loadMoreButton.className = 'interactive-border';
            loadMoreButton.textContent = 'Load More';
            loadMoreButton.onclick = () => fetchAndDisplayImages(false);
            outputArea.appendChild(loadMoreButton);
            addInteractiveBorderListeners(loadMoreButton);
        }
    }

    function copyUrlToClipboard(url, button) {
        navigator.clipboard.writeText(url).then(() => {
            button.innerHTML = '<i class="fa-solid fa-check"></i>';
            setTimeout(() => {
                button.innerHTML = '<i class="fa-solid fa-copy"></i>';
            }, 1500);
        });
    }

    function updateProgress(percentage, status) {
        progressBar.style.width = `${percentage}%`;
        progressStatus.textContent = status;
    }

    function showError(message) {
        outputArea.innerHTML = `<div class="error-box">${message}</div>`;
    }

    function openLightbox(index) {
        currentLightboxIndex = index;
        lightboxImage.src = allImageUrls[index];
        lightbox.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeLightbox() {
        lightbox.classList.add('hidden');
        document.body.style.overflow = '';
    }

    function changeLightboxImage(direction) {
        currentLightboxIndex += direction;
        if (currentLightboxIndex < 0) currentLightboxIndex = allImageUrls.length - 1;
        if (currentLightboxIndex >= allImageUrls.length) currentLightboxIndex = 0;
        lightboxImage.src = allImageUrls[currentLightboxIndex];
    }

    lightbox.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
    lightbox.querySelector('.lightbox-prev').addEventListener('click', () => changeLightboxImage(-1));
    lightbox.querySelector('.lightbox-next').addEventListener('click', () => changeLightboxImage(1));
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
        if (lightbox.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') changeLightboxImage(-1);
        if (e.key === 'ArrowRight') changeLightboxImage(1);
    });

    applySavedPreferences();

    const urlParams = new URLSearchParams(window.location.search);
    const queryFromUrl = urlParams.get('query');
    if (queryFromUrl) {
        queryInput.value = decodeURIComponent(queryFromUrl);
        startSearch(queryFromUrl);
    }
});
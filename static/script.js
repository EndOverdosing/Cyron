document.addEventListener('DOMContentLoaded', () => {
    const queryInput = document.getElementById('query-input');
    const numImagesSelect = document.getElementById('num-images-select');
    const submitButton = document.getElementById('submit-button');
    const searchForm = document.getElementById('search-form');
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

    async function startDownload(event) {
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
            const response = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    num_images: numImagesSelect.value,
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Server error: ${response.statusText}`);
            }

            updateProgress(75, "Packaging images into a ZIP file...");
            const blob = await response.blob();

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'images.zip';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="(.+)"/);
                if (filenameMatch && filenameMatch.length > 1) {
                    filename = filenameMatch[1];
                }
            }

            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();

            updateProgress(100, "Download started!");
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                showSuccess(`Your download for "${query}" has started.`);
            }, 1000);

        } catch (e) {
            console.error("Error:", e);
            showError(e.message);
            progressContainer.classList.add('hidden');
        } finally {
            submitButton.disabled = false;
        }
    }

    window.startDownload = startDownload;

    function updateProgress(percentage, status) {
        progressBar.style.width = `${percentage}%`;
        progressStatus.textContent = status;
    }

    function showSuccess(message) {
        outputArea.innerHTML = `
            <div class="result-card">
                <div class="result-info">
                    <h2>Success!</h2>
                    <div id="download-status">${message}</div>
                </div>
            </div>
        `;
    }

    function showError(message) {
        outputArea.innerHTML = `<div class="error-box">${message}</div>`;
    }

    applySavedPreferences();
});
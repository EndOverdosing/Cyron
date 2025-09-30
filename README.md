![Rylox Logo](/static/assets/banner.png)

# Cyron - Image Search Engine



Cyron is a sleek, privacy-respecting image search engine that delivers stunning visuals, instantly. It leverages a network of public SearX instances to fetch image results without tracking the user, wrapped in a modern, dynamic user interface.

## Features

-   **Privacy-Focused Backend**: Aggregates results from multiple SearX instances, ensuring user privacy and anonymity.
-   **Modern UI**: A clean, glassmorphism-inspired design with light and dark themes.
-   **Advanced Search Filters**: Filter results by image size, time range, and a toggle for Safe Search.
-   **Dynamic Image Grid**: A beautiful, masonry-style layout for displaying image results.
-   **Interactive Lightbox**: View images in a full-screen lightbox with easy navigation between results.
-   **Client-Side Routing**: The browser URL updates with your search query for easy sharing and bookmarking.
-   **Persistent Preferences**: Your selected theme and filter choices are saved in your browser for future visits.
-   **Infinite Scroll**: A "Load More" button allows you to seamlessly load subsequent pages of results.
-   **Robust Error Handling**: Gracefully handles broken image links and notifies the user if no more results can be found.

## Tech Stack

-   **Frontend**: HTML5, CSS3, Vanilla JavaScript (No frameworks)
-   **Backend**: Python 3, Flask
-   **API**: Aggregates data from public SearX meta-search engine instances.
-   **Deployment**: Vercel

## Getting Started

To run this project on your local machine, follow these steps.

### Prerequisites

-   Python 3.8 or newer
-   `pip` (Python package installer)
-   Git

### Local Development Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/cyron-image-search.git
    cd cyron-image-search
    ```

2.  **Create and activate a virtual environment:**
    -   **Windows:**
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    -   **macOS / Linux:**
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the Flask application:**
    ```sh
    flask run
    ```

5.  Open your web browser and navigate to `http://127.0.0.1:5000`.

## Deployment

This project is configured for easy deployment on **Vercel**.

1.  **Sign up** for a free account at [vercel.com](https://vercel.com).
2.  **Create a new project** and connect it to your GitHub repository where you've pushed this code.
3.  **Configure the project**: Vercel will automatically detect that this is a Python project and use the `vercel.json` file for configuration. No changes should be necessary. The root directory and build commands will be pre-filled.
4.  **Deploy**: Click the "Deploy" button. Vercel will handle the entire build process and provide you with a live URL.

## Project Structure

```
/
├── app.py              # Flask backend server and API logic
├── requirements.txt    # Python dependencies for pip
├── vercel.json         # Vercel deployment configuration
├── .gitignore          # Files to be ignored by Git
│
├── templates/
│   └── index.html      # The main HTML structure of the application
│
└── static/
    ├── script.js       # All frontend JavaScript logic
    ├── style.css       # All application styles
    └── assets/         # Folder for static assets like logos or banners
```
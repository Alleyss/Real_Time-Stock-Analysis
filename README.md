# Stock Sentiment Analysis Application

This application fetches stock data using `yfinance`, analyzes news sentiment using `newspaper3k`, and provides buy/sell/hold suggestions based on stock sentiment. The app is built with a FastAPI backend and a Next.js frontend.

## Features

- Real-time stock data fetching using `yfinance`.
- News sentiment analysis using `newspaper3k` and external news sources via `newsapi`.
- Buy/Sell/Hold recommendations based on sentiment analysis.
- User authentication, stock search, and portfolio features.

## Installation

### Backend Setup

1. Navigate to the `backend` directory:

    ```bash
    cd backend
    ```

2. Install required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the FastAPI backend server:

    ```bash
    uvicorn app.main:app --reload
    ```

   The server will start at `http://127.0.0.1:8000`.

### Frontend Setup

1. Navigate to the `stock-analyzer-frontend` directory:

    ```bash
    cd stock-analyzer-frontend
    ```

2. Install required dependencies:

    ```bash
    npm install
    ```

3. Run the frontend development server:

    ```bash
    npm run dev
    ```

   The frontend will be accessible at `http://localhost:3000`.

### Additional Dependencies for Frontend

If needed, install the following dependencies:

```bash
npm install react-loading-skeleton
npm install react-hot-toast

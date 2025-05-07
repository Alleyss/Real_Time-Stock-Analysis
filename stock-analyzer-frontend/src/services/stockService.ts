// src/services/stockService.ts
import apiClient from './api';
// Import the necessary response types from your types definition
import type { StockInfo, SentimentAnalysisResult, AnalyzedItem, JustificationPoint } from '../types/stock'; // Adjust path if needed
import type { SentimentDataSource } from '../types/common'; // Import the Enum type if defined separately

// Fetch basic stock information
export const getStockInfo = async (tickerSymbol: string): Promise<StockInfo> => {
    try {
        const upperTicker = tickerSymbol.toUpperCase();
        const response = await apiClient.get<StockInfo>(`/stocks/${upperTicker}/info`);
        return response.data;
    } catch (error: any) {
        console.error(`Error fetching stock info for ${tickerSymbol}:`, error);
        // Return a structure indicating error, matching StockInfo schema if possible
        const detail = error.response?.data?.detail || `Failed to fetch info for ${tickerSymbol}`;
         return {
             symbol: tickerSymbol.toUpperCase(),
             company_name: "N/A",
             current_price: "N/A",
             error: detail
         };
        // Or rethrow a more specific error
        // throw new Error(detail);
    }
};

// Fetch sentiment analysis results
export const getSentimentAnalysis = async (
    tickerSymbol: string,
    source: SentimentDataSource | string // Allow string for flexibility, but enum is better
    ): Promise<SentimentAnalysisResult> => {
    try {
        const upperTicker = tickerSymbol.toUpperCase();
        // Ensure source value is sent correctly (e.g., 'news', 'reddit')
        const sourceValue = typeof source === 'string' ? source : source.valueOf();
        const response = await apiClient.get<SentimentAnalysisResult>(`/stocks/${upperTicker}/sentiment`, {
            params: { source: sourceValue } // Pass source as query parameter
        });
        return response.data;
    } catch (error: any) {
        console.error(`Error fetching ${source} sentiment for ${tickerSymbol}:`, error);
        const detail = error.response?.data?.detail || `Failed to fetch ${source} sentiment for ${tickerSymbol}`;
        // You might want to define a default error structure for SentimentAnalysisResult
         throw new Error(detail); // Rethrow for the component to handle
    }
};
// src/types/stock.ts (Example based on your backend schemas)
export interface StockInfo {
    symbol: string;
    company_name: string;
    current_price: number | string | null;
    currency?: string | null;
    sector?: string | null;
    industry?: string | null;
    market_cap?: number | null;
    error?: string | null;
    // info?: any; // Add if you plan to use the raw info
}

export interface AnalyzedItem {
    headline?: string | null;
    url?: string | null;
    score: number;
    label: string;
    publishedAt?: string | null;
    source_name?: string | null;
    source_type?: string | null;
    source_specific_id?: string | null; // Good to have if needed later
}

export interface JustificationPoint {
    type: string;
    headline?: string | null;
    url?: string | null;
    source?: string | null;
    score?: number | null;
}

export interface SentimentAnalysisResult {
    ticker: string;
    company_name: string;
    data_source: string;
    aggregated_score: number;
    suggestion: string;
    analyzed_articles_count: number;
    justification_points: JustificationPoint[];
    top_analyzed_items: AnalyzedItem[];
}
// src/pages/StockDetailPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getStockInfo, getSentimentAnalysis } from '../services/stockService';
import { addToWishlist, removeFromWishlist, checkWishlistItem } from '../services/wishlistService';
import type { StockInfo, SentimentAnalysisResult, AnalyzedItem } from '../types/stock';
import { SentimentDataSource } from '../types/common'; // Your Enum
import Button from '../components/common/Button'; // Your Button component
import LoadingSpinner from '../components/common/LoadingSpinner'; // We'll create this simple component

const StockDetailPage: React.FC = () => {
    const { ticker } = useParams<{ ticker: string }>();
    const upperTicker = ticker?.toUpperCase() || 'N/A';

    const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
    const [sentimentResult, setSentimentResult] = useState<SentimentAnalysisResult | null>(null);
    const [isInWishlist, setIsInWishlist] = useState<boolean | null>(null); // null indicates loading state
    const [infoLoading, setInfoLoading] = useState<boolean>(true);
    const [sentimentLoading, setSentimentLoading] = useState<boolean>(false);
    const [wishlistLoading, setWishlistLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // --- Data Fetching Callbacks ---
    const fetchInfo = useCallback(async () => {
        if (!ticker) return;
        setInfoLoading(true);
        setError(null);
        try {
            const info = await getStockInfo(ticker);
            setStockInfo(info);
            if(info.error) {
                 setError(`Info: ${info.error}`); // Show yfinance errors if any
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load stock info.');
            console.error("Fetch Info Error:", err);
        } finally {
            setInfoLoading(false);
        }
    }, [ticker]);

    const fetchSentiment = useCallback(async (source: SentimentDataSource) => {
        if (!ticker) return;
        setSentimentLoading(true);
        setError(null);
        setSentimentResult(null); // Clear previous results
        try {
            const result = await getSentimentAnalysis(ticker, source);
            setSentimentResult(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : `Failed to load ${source} sentiment.`);
            console.error(`Fetch ${source} Sentiment Error:`, err);
        } finally {
            setSentimentLoading(false);
        }
    }, [ticker]);

    const checkWishlistStatus = useCallback(async () => {
        if (!ticker) return;
        setWishlistLoading(true); // Indicate wishlist check is loading
        // setError(null); // Maybe don't clear general error for this check
        try {
            const item = await checkWishlistItem(ticker);
            setIsInWishlist(!!item); // Set to true if item exists, false otherwise
        } catch (err) {
            // This check might fail if backend doesn't have a specific endpoint
            // Or if user is logged out (handled by protected route, but good check)
            console.error("Error checking wishlist status:", err);
            setIsInWishlist(null); // Set back to null on error? Or false? Depends on desired UX
        } finally {
            setWishlistLoading(false);
        }
    }, [ticker]);


    // --- Effects ---
    useEffect(() => {
        // Fetch stock info and check wishlist status when ticker changes
        fetchInfo();
        checkWishlistStatus();
        setSentimentResult(null); // Clear sentiment when ticker changes
    }, [fetchInfo, checkWishlistStatus]); // Depend on the memoized functions

    // --- Event Handlers ---
    const handleWishlistToggle = async () => {
        if (!ticker || wishlistLoading || isInWishlist === null) return;
        setWishlistLoading(true);
        setError(null);
        try {
            if (isInWishlist) {
                await removeFromWishlist(ticker);
                setIsInWishlist(false);
            } else {
                await addToWishlist(ticker);
                setIsInWishlist(true);
            }
        } catch (err) {
             setError(err instanceof Error ? err.message : 'Failed to update wishlist.');
             console.error("Wishlist Toggle Error:", err);
             // Re-check actual status on error?
             checkWishlistStatus(); // Re-fetch status to be sure
        } finally {
             // Wishlist loading state is handled by checkWishlistStatus now if called on error
             // setWishlistLoading(false); // Only set false if checkWishlistStatus isn't called
        }
    };


    // --- Rendering Logic ---
    const renderAnalyzedItem = (item: AnalyzedItem) => {
        const emoji = item.label === 'positive' ? '🟢' : item.label === 'negative' ? '🔴' : '⚪️';
        return (
            <li key={item.url || item.headline} className="py-2 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                <a href={item.url || '#'} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-600 dark:text-blue-400 text-sm">
                    {emoji} {item.headline || 'No Headline Available'}
                </a>
                <span className="text-xs text-gray-500 dark:text-gray-400 block">
                    Source: {item.source_name || 'N/A'} | Score: {item.score.toFixed(2)}
                </span>
            </li>
        );
    };

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-2 flex items-center">
                {infoLoading ? <LoadingSpinner size="h-8 w-8" /> : stockInfo?.company_name || 'Stock Details'}
                <span className="ml-3 text-blue-600 dark:text-blue-400">{upperTicker}</span>
            </h1>
             {error && <p className="text-red-500 text-center text-sm mb-4 p-2 bg-red-100 dark:bg-red-900 rounded">{error}</p>}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* --- Column 1: Stock Info & Wishlist --- */}
                <div className="md:col-span-1 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md self-start">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">Stock Info</h2>
                    {infoLoading ? (
                        <LoadingSpinner />
                    ) : stockInfo && !stockInfo.error ? (
                        <div className="space-y-2 text-sm">
                            <p><strong>Company:</strong> {stockInfo.company_name}</p>
                            <p><strong>Price:</strong> {typeof stockInfo.current_price === 'number' ? `${stockInfo.currency || '$'}${stockInfo.current_price.toFixed(2)}` : stockInfo.current_price}</p>
                            <p><strong>Sector:</strong> {stockInfo.sector || 'N/A'}</p>
                            <p><strong>Industry:</strong> {stockInfo.industry || 'N/A'}</p>
                            <p><strong>Market Cap:</strong> {stockInfo.market_cap ? `$${stockInfo.market_cap.toLocaleString()}` : 'N/A'}</p>
                        </div>
                    ) : (
                        <p className="text-gray-500 dark:text-gray-400">
                           {stockInfo?.error || "Could not load stock information."}
                        </p>
                    )}
                    {/* Wishlist Button */}
                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <Button
                            onClick={handleWishlistToggle}
                            isLoading={wishlistLoading}
                            disabled={isInWishlist === null || infoLoading || !!stockInfo?.error} // Disable if loading status or if stock info failed
                            variant={isInWishlist ? 'secondary' : 'primary'}
                            className="w-full"
                        >
                            {isInWishlist === null ? 'Checking Wishlist...' : isInWishlist ? 'Remove from Wishlist' : 'Add to Wishlist'}
                        </Button>
                    </div>
                </div>

                {/* --- Column 2: Sentiment Analysis --- */}
                <div className="md:col-span-2 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">Sentiment Analysis</h2>
                    <div className="flex space-x-4 mb-6">
                        <Button
                           onClick={() => fetchSentiment(SentimentDataSource.NEWS)}
                           isLoading={sentimentLoading}
                           disabled={sentimentLoading || infoLoading || !!stockInfo?.error} // Disable if loading or stock info failed
                           className="flex-1"
                        >
                            Analyze News 📰
                        </Button>
                         <Button
                           onClick={() => fetchSentiment(SentimentDataSource.REDDIT)}
                           isLoading={sentimentLoading}
                           disabled={sentimentLoading || infoLoading || !!stockInfo?.error}
                           className="flex-1"
                        >
                            Analyze Reddit 👽
                        </Button>
                    </div>

                    {/* Sentiment Results Display Area */}
                    {sentimentLoading ? (
                        <div className="text-center py-8">
                            <LoadingSpinner text="Analyzing sentiment..." />
                        </div>
                    ) : sentimentResult ? (
                        <div className="space-y-4">
                           {/* Summary Section */}
                           <div className="p-4 rounded bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600">
                               <h3 className="font-semibold text-lg mb-2">Analysis Summary ({sentimentResult.data_source})</h3>
                               <div className="flex justify-between items-center text-sm mb-1">
                                   <span>Aggregated Score:</span>
                                   <span className={`font-bold ${sentimentResult.aggregated_score > 0.05 ? 'text-green-600 dark:text-green-400' : sentimentResult.aggregated_score < -0.05 ? 'text-red-600 dark:text-red-400' : ''}`}>
                                      {sentimentResult.aggregated_score.toFixed(3)}
                                   </span>
                               </div>
                               <div className="flex justify-between items-center text-sm">
                                   <span>Suggestion:</span>
                                   <span className="font-bold">{sentimentResult.suggestion}</span>
                               </div>
                               <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Based on {sentimentResult.analyzed_articles_count} analyzed items.</p>
                           </div>

                            {/* Justification Points */}
                           {sentimentResult.justification_points && sentimentResult.justification_points.length > 0 && (
                               <div>
                                   <h4 className="font-semibold mb-2 text-gray-700 dark:text-gray-300">Justification Points:</h4>
                                   <ul className="space-y-2 text-xs list-disc list-inside pl-2">
                                        {sentimentResult.justification_points.map((point, index) => {
                                            const emoji = point.type === 'positive' ? '🟢' : point.type === 'negative' ? '🔴' : '⚪️';
                                            return (
                                                <li key={index}>
                                                    {emoji} <a href={point.url || '#'} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-600 dark:text-blue-400">{point.headline || 'N/A'}</a> ({point.source || 'N/A'}, Score: {point.score?.toFixed(2) ?? 'N/A'})
                                                </li>
                                            );
                                        })}
                                   </ul>
                               </div>
                           )}

                            {/* Top Analyzed Items List */}
                           {sentimentResult.top_analyzed_items && sentimentResult.top_analyzed_items.length > 0 && (
                               <div>
                                   <h4 className="font-semibold mb-2 text-gray-700 dark:text-gray-300">Top Analyzed Items:</h4>
                                   <ul className="space-y-1 max-h-80 overflow-y-auto pr-2"> {/* Scrollable list */}
                                       {sentimentResult.top_analyzed_items.map(renderAnalyzedItem)}
                                   </ul>
                               </div>
                           )}
                        </div>
                    ) : (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                           Select a source (News or Reddit) to perform sentiment analysis.
                        </p>
                    )}
                </div> {/* End Sentiment Analysis Column */}
            </div> {/* End Grid */}
        </div> // End Page Wrapper
    );
};

export default StockDetailPage;
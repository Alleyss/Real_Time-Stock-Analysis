// src/utils/formatters.ts

/**
 * Formats a large number into a more readable string with suffixes (K, M, B, T).
 * Handles null or undefined inputs gracefully.
 * Example: 1_234_567 -> "1.23M"
 * Example: 5432 -> "5.43K"
 */
export const formatLargeNumber = (num: number | null | undefined): string => {
    if (num === null || num === undefined || isNaN(num)) {
        return 'N/A';
    }
    if (num === 0) { return '0'; }

    const absNum = Math.abs(num);
    let formattedNum: string;

    if (absNum >= 1e12) { // Trillions
        formattedNum = (num / 1e12).toFixed(2) + 'T';
    } else if (absNum >= 1e9) { // Billions
        formattedNum = (num / 1e9).toFixed(2) + 'B';
    } else if (absNum >= 1e6) { // Millions
        formattedNum = (num / 1e6).toFixed(2) + 'M';
    } else if (absNum >= 1e3) { // Thousands
        formattedNum = (num / 1e3).toFixed(2) + 'K';
    } else {
        formattedNum = num.toFixed(2); // Keep precision for smaller numbers if needed
    }

    // Optional: Remove trailing '.00'
    return formattedNum.replace(/\.00([TBMK])$/, '$1').replace(/\.00$/, '');
};

/**
 * Formats a number as currency.
 * Handles null or undefined inputs.
 * Includes basic currency symbol handling.
 */
export const formatCurrency = (
    value: number | null | undefined,
    currencySymbol: string | null | undefined = '$', // Default to USD
    locale: string = 'en-US' // For potential future locale-specific formatting
): string => {
    if (value === null || value === undefined || isNaN(value)) {
        return 'N/A';
    }
    
    // Basic formatting, can be expanded with Intl.NumberFormat for more complex needs
    const symbol = currencySymbol || '';
    return `${symbol}${value.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    // Alternative using Intl.NumberFormat (more robust but slightly more complex setup)
    /*
    try {
        const options: Intl.NumberFormatOptions = {
            style: 'currency',
            currency: currencyCode || 'USD', // Requires a valid ISO 4217 currency code
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        };
        return new Intl.NumberFormat(locale, options).format(value);
    } catch (e) {
        console.error("Currency formatting error:", e);
        // Fallback to basic formatting
        return `${currencySymbol || '$'}${value.toFixed(2)}`;
    }
    */
};
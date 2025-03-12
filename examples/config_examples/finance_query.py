#!/usr/bin/env python
"""
Query script for the finance configuration.
This script demonstrates how to use the cryptocurrency and stock market MCP servers together.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("finance-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def get_crypto_prices(symbols, config):
    """Get cryptocurrency prices."""
    # In a real implementation, this would use the MCP client to call the cryptocurrency server
    logger.info(f"Getting cryptocurrency prices for {symbols}")
    
    # Simulate the cryptocurrency data
    crypto_data = []
    for symbol in symbols:
        price = 0
        if symbol.lower() == "btc":
            price = 65000.0
        elif symbol.lower() == "eth":
            price = 3500.0
        elif symbol.lower() == "sol":
            price = 150.0
        else:
            price = 10.0  # Default price for unknown symbols
        
        crypto_data.append({
            "symbol": symbol.upper(),
            "name": {
                "btc": "Bitcoin",
                "eth": "Ethereum",
                "sol": "Solana"
            }.get(symbol.lower(), f"Unknown ({symbol})"),
            "price_usd": price,
            "market_cap": price * 1000000,
            "volume_24h": price * 100000,
            "change_24h": 2.5 if symbol.lower() == "btc" else -1.2 if symbol.lower() == "eth" else 5.7,
            "last_updated": "2025-03-11T10:00:00Z"
        })
    
    return crypto_data

def get_stock_prices(symbols, config):
    """Get stock prices."""
    # In a real implementation, this would use the MCP client to call the stock market server
    logger.info(f"Getting stock prices for {symbols}")
    
    # Simulate the stock data
    stock_data = []
    for symbol in symbols:
        price = 0
        if symbol.lower() == "aapl":
            price = 200.0
        elif symbol.lower() == "msft":
            price = 400.0
        elif symbol.lower() == "googl":
            price = 150.0
        else:
            price = 50.0  # Default price for unknown symbols
        
        stock_data.append({
            "symbol": symbol.upper(),
            "name": {
                "aapl": "Apple Inc.",
                "msft": "Microsoft Corporation",
                "googl": "Alphabet Inc."
            }.get(symbol.lower(), f"Unknown ({symbol})"),
            "price": price,
            "change": 1.2 if symbol.lower() == "aapl" else 0.8 if symbol.lower() == "msft" else -0.5,
            "change_percent": 0.6 if symbol.lower() == "aapl" else 0.2 if symbol.lower() == "msft" else -0.3,
            "market_cap": price * 1000000000,
            "pe_ratio": 25.0 if symbol.lower() == "aapl" else 30.0 if symbol.lower() == "msft" else 20.0,
            "dividend_yield": 0.5 if symbol.lower() == "aapl" else 0.8 if symbol.lower() == "msft" else 0.0,
            "last_updated": "2025-03-11T16:00:00Z"
        })
    
    return stock_data

def format_crypto_data(crypto_data):
    """Format the cryptocurrency data for display."""
    output = []
    output.append("Cryptocurrency Prices:")
    
    for crypto in crypto_data:
        output.append(f"\n  {crypto['name']} ({crypto['symbol']}):")
        output.append(f"    Price: ${crypto['price_usd']:,.2f}")
        output.append(f"    Market Cap: ${crypto['market_cap']:,.0f}")
        output.append(f"    24h Volume: ${crypto['volume_24h']:,.0f}")
        output.append(f"    24h Change: {crypto['change_24h']:+.2f}%")
        output.append(f"    Last Updated: {crypto['last_updated']}")
    
    return "\n".join(output)

def format_stock_data(stock_data):
    """Format the stock data for display."""
    output = []
    output.append("\nStock Prices:")
    
    for stock in stock_data:
        output.append(f"\n  {stock['name']} ({stock['symbol']}):")
        output.append(f"    Price: ${stock['price']:,.2f}")
        output.append(f"    Change: {stock['change']:+.2f} ({stock['change_percent']:+.2f}%)")
        output.append(f"    Market Cap: ${stock['market_cap']:,.0f}")
        output.append(f"    P/E Ratio: {stock['pe_ratio']:.2f}")
        output.append(f"    Dividend Yield: {stock['dividend_yield']:.2f}%")
        output.append(f"    Last Updated: {stock['last_updated']}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query financial data.")
    parser.add_argument("--crypto", default="BTC,ETH,SOL", help="Comma-separated list of cryptocurrency symbols")
    parser.add_argument("--stocks", default="AAPL,MSFT,GOOGL", help="Comma-separated list of stock symbols")
    parser.add_argument("--config", default="finance_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Parse the symbols
    crypto_symbols = args.crypto.split(",")
    stock_symbols = args.stocks.split(",")
    
    # Get the cryptocurrency and stock data
    crypto_data = get_crypto_prices(crypto_symbols, config)
    stock_data = get_stock_prices(stock_symbols, config)
    
    # Format and display the results
    print(format_crypto_data(crypto_data))
    print(format_stock_data(stock_data))

if __name__ == "__main__":
    main()

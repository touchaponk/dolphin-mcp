# examples

## sqlite

```dolphin-mcp-cli --mcp-config examples/sqlite-mcp.json  --model dolphin "Explore the database, and choose one random row - and write a story about it"```

## filesystem-fetch

```dolphin-mcp-cli --mcp-config examples/filesystem-fetch-mcp.json --model gpt-4o "Read ./examples/stocklist.txt and fetch https://finance.yahoo.com/topic/stock-market-news/. If there is positive news about any of the stocks in the list, advise me to buy that stock.  if there is negative news about any of the stocks in the list, advise me to sell that stock."```


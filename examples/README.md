# examples

## sqlite

```dolphin-mcp-cli --mcp-config examples/sqlite-mcp.json  --model dolphin "Explore the database, and choose one random row - and write a story about it"```

### Output

```
[OK] dolphin-demo-database-sqlite

View result from list_tables from dolphin-demo-database-sqlite {}
{
  "content": [
    {
      "type": "text",
      "text": "[{'name': 'dolphin_species'}, {'name': 'evolutionary_relationships'}, {'name': 'table_name'}]"
    }
  ],
  "isError": false
}

View result from read_query from dolphin-demo-database-sqlite {"query": "SELECT * FROM dolphin_species ORDER BY RANDOM() LIMIT 1"}
{
  "content": [
    {
      "type": "text",
      "text": "[{'id': 3, 'common_name': 'Common Dolphin', 'scientific_name': 'Delphinus delphis', 'family': 'Delphinidae', 'habitat': 'Oceanic', 'average_length_meters': 2.3, 'average_weight_kg': 110.0, 'average_lifespan_years': 35, 'conservation_status': 'Least Concern', 'population_estimate': 'Unknown', 'evolutionary_ancestor': 'Kentriodontids', 'description': 'Known for their distinctive colorful pattern and hourglass pattern on their sides.'}]"
    }
  ],
  "isError": false
}

In the vast expanse of the ocean, where the sun kisses the water in a golden embrace, there swims a creature of grace and beauty. Meet the Common Dolphin, Delphinus delphis, a marvel of nature that has captivated human hearts for centuries.

Our story begins with an individual dolphin, one whose life is as mysterious as the depths from which it emerges. This particular dolphin, measuring 2.3 meters in length and weighing around 110 kilograms, is a testament to the resilience and adaptability of its species. It belongs to the family Delphinidae, a group renowned for their intelligence and playful nature.

The Common Dolphin's habitat is as boundless as the ocean itself, preferring the open waters where it can swim freely without constraint. Its average lifespan of 35 years speaks of a life filled with adventure and exploration, a journey through the highs and lows of the sea.

But what sets this dolphin apart is not just its physical attributes or its habitat; it is the story of its evolutionary past. This dolphin's ancestors were once Kentriodontids, ancient creatures that roamed the oceans millions of years ago. Over time, they evolved into the sleek and sophisticated beings we know today.

As our dolphin glides through the water, its sides adorned with a distinctive colorful pattern and an hourglass shape, it is a living testament to the power of evolution. Its conservation status as 'Least Concern' is a beacon of hope, a sign that despite the challenges faced by many marine species, this one thrives.

Yet, there is still much we do not know about our dolphin friend. The population estimate remains a mystery, a secret hidden beneath the waves. But what we do know is enough to inspire awe and wonder.

In the heart of the ocean, where the unknown awaits around every corner, our Common Dolphin swims on. Its story is one of survival, adaptation, and beauty, a reminder of the magic that lies just beyond our reach in the depths of the sea.

```

## filesystem-fetch

```dolphin-mcp-cli --mcp-config examples/filesystem-fetch-mcp.json --model gpt-4o "Read ./examples/stocklist.txt and fetch https://finance.yahoo.com/topic/stock-market-news/. If there is positive news about any of the stocks in the list, advise me to buy that stock.  if there is negative news about any of the stocks in the list, advise me to sell that stock."```

### Output

## 



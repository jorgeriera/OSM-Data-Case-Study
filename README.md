# OpenStreetMap Data Case Study

### Map Area
Miami,Florida, United States

- [https://www.openstreetmap.org/#map=12/25.7588/-80.2180](https://www.openstreetmap.org/#map=12/25.7588/-80.2180)

This is a map of my hometown from an open source mapping site called OpenStreetMap. Users are able to contribute to the map as they see fit. Given that it is a collaborative map, it is especially prone to human error. I would like to access the quality of the data for this subsect and determine if there are any necessary changes. 


## Problems Encountered in the Map
After initially downloading a small sample size of the Charlotte area and running it against a provisional data.py file, I noticed five main problems with the data, which I will discuss in the following order:


- Over­abbreviated street names *(“S Tryon St Ste 105”)*
- Inconsistent postal codes *(“NC28226”, “28226­0783”, “28226”)*
- “Incorrect” postal codes (Charlotte area zip codes all begin with “282” however a large portion of all documented zip codes were outside this region.)
- Second­ level `“k”` tags with the value `"type"`(which overwrites the element’s previously processed `node[“type”]field`).
- Street names in second ­level `“k”` tags pulled from Tiger GPS data and divided into segments, in the following format:

	```XML
	<tag k="tiger:name_base" v="Stonewall"/> 
	<tag k="tiger:name_direction_prefix" v="W"/> 
	<tag k="tiger:name_type" v="St"/>
	```

### Over­abbreviated Street Names
Once the data was imported to SQL, some basic querying revealed street name abbreviations and postal code inconsistencies. To deal with correcting street names, I opted not use regular expressions, and instead iterated over each word in an address, correcting them to their respective mappings in audit.py using the following function:

```python 
def update(name, mapping): 
	words = name.split()
	for w in range(len(words)):
		if words[w] in mapping:
			if words[w­1].lower() not in ['suite', 'ste.', 'ste']: 
				# For example, don't update 'Suite E' to 'Suite East'
				words[w] = mapping[words[w]] name = " ".join(words)
	return name
```

This updated all substrings in problematic address strings, such that:
*“S Tryon St Ste 105”*
becomes:
*“South Tryon Street Suite 105”*

### Postal Codes
Postal code strings posed a different sort of problem, forcing a decision to strip all leading and trailing characters before and after the main 5­digit zip code. This effectively dropped all leading state characters (as in “NC28226”) and 4­digit zip code extensions following a hyphen (“28226­0783”). This 5­digit restriction allows for more consistent queries.


Regardless, after standardizing inconsistent postal codes, some altogether “incorrect” (or perhaps misplaced?) postal codes surfaced when grouped together with this aggregator:

```sql
SELECT tags.value, COUNT(*) as count 
FROM (SELECT * FROM nodes_tags 
	  UNION ALL 
      SELECT * FROM ways_tags) tags
WHERE tags.key='postcode'
GROUP BY tags.value
ORDER BY count DESC;
```

Here are the top ten results, beginning with the highest count:

```sql
value|count
28205|900
28208|388
28206|268
28202|204
28204|196
28216|174
28211|148
28203|120
28209|104
28207|86
```

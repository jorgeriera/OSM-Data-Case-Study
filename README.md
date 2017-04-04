 OpenStreetMap Data Case Study

### Map Area
Miami,Florida, United States

- [https://www.openstreetmap.org/#map=12/25.7588/-80.2180](https://www.openstreetmap.org/#map=12/25.7588/-80.2180)

This is a map of my hometown from an open source mapping site called OpenStreetMap. Users are able to contribute to the map as they see fit. Given that it is a collaborative map, it is especially prone to human error. I would like to access the quality of the data for this subsect and determine if there are any necessary changes.

### Boundary

The first thing I did after loading the dataset was to check if the node values were within the boundaries of the map. First I found the boundary element from the XML source file I was working with, and I found the maximum and minimum values for latitude/longitude. Then I looped through each node element and compared the lat/lon values to their respective values. This test did not yield any errors.

```XML
	<bounds minlat="25.6692244" minlon="-80.4231834" maxlat="25.87093" maxlon="-80.115347"/>
	```

```Python
def map_boundary(filename):
    for _, element in ET.iterparse(filename):
        if element.tag == "bounds":
            minlat=float(element.attrib['minlat'])
            minlon=float(element.attrib['minlon'])
            maxlat=float(element.attrib['maxlat'])
            maxlon=float(element.attrib['maxlon'])
            #print y['minlat']
            return minlat,minlon,maxlat,maxlon

def boundary_check(filename):
    errors={'wrong_coordinates':0}
    minlat,minlon,maxlat,maxlon=map_boundary(filename)
    for _, element in ET.iterparse(filename):
        if element.tag == "node":
            if (float(element.attrib['lat'])<minlat) or (float(element.attrib['lat'])>maxlat):
                print element.attrib['lat']
                break
                errors['wrong_coordinates']+=1
            elif (float(element.attrib['lon'])<minlon) or (float(element.attrib['lon'])>maxlon):
                errors['wrong_coordinates']+=1
    return errors
```
### Street Names

Next I checked for inconsistencies in street names.

```Python
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons","Causeway","Passage","Way",'Circle','Highway','Plaza','Terrace']


mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Ave.": "Avenue",
            "Cirlce": "Circle",
            "Hwy": "Highway",
            "Dr": "Drive",
            "PL": "Place",
            "Blvd":"Boulevard"
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
    return street_types


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types.keys()

```

I found a number of discrepancies in the naming conventions of street name values. I found the following exceptions:

|Exceptions|    |       |
|---	|---	|---	|
| St. 	|  Dr	|  	Ct|
| Rd 	|  PL	|  Ave	|
|  Pl	| Ave. 	| Blvd 	|
| Hwy 	|  St	| ST 	|

After singling out what had to be changed, I mapped out what each exception value should be replaced to and corrected the inconsistencies:

```Python
def audit_street_type(street_name,mapping):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            print street_type
            street_name=update_name(street_name,mapping)
            print street_name
    return street_name
    
def update_name(name, mapping):
    m=street_type_re.search(name)
    if m.group() in mapping.keys():
        name=name[:len(name)-len(m.group())]+mapping[m.group()]
    return name
    
  ```
  
 
### Cardinal Directions
A typical inconsistency found in addresses is the representation of a given cardinal direction. I tested for this in the Miami OSM sample database under the way/node tags and found a number of variations in the street name values. For example, North is written as: N,N., and North.

```Python
direction=['Southwest','Southeast','Northwest','Northeast', 'North','South','East','West']

direction_mapping={"N.W.": "Northwest",
            "N.E": "Northeast",
            "S.E.": "Southeast",
            "S.W.": "Southwest",
            "NW": "Northwest",
            "NE": "Northeast",
            "SW": "Southwest",
            "SE": "Southeast",
            "N": "North",
            "S": "South",
            "W": "West",
            "E": "East",
            "N.": "North",
            "S.": "South",
            "W.": "West",
            "E.": "East",
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
    return street_types


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    audit_direction=set()
    osm_file = open(osmfile, "r")
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):

                if is_street_name(tag) and (tag.attrib['v'].split(' ')[0] not in direction) and (len(tag.attrib['v'].split(' ')[0])<5):
                    audit_direction.update([tag.attrib['v'].split(' ')[0]])
                    
    osm_file.close()
    return audit_direction
```
    
After running this code I singled out which values were cardinal directions and added these to a new list called abbv_direction. I modified my code to exclude any results from this new list. The new audit function did not yield any new abbreviated values. 

```Python
abbv_direction=['N.W.','N.E.','S.E.','S.W.','NW','NE','SW','SE','N','S','W','E','N.','S.','E.','W.']
...
if is_street_name(tag) and (tag.attrib['v'].split(' ')[0] not in abbv_direction 
                    and tag.attrib['v'].split(' ')[0] not in direction) and (len(tag.attrib['v'].split(' ')[0])<5):
                    audit_direction.update([tag.attrib['v'].split(' ')[0])
```
After singling out possible variations, I standardized the data using the update_direction function:

```Python
def update_direction(name,mapping):
    name_val=name.attrib['v']
    abbv=name.attrib['v'].split(' ')[0]
    name=mapping[abbv]+name_val[len(abbv):]
    return name
```
## Exploring Data
The following section is an overview of the technical specificaitons of the Miami OSM dataset as well some findings from my data querying.

### File sizes
```
miami.osm ............ 169.3 MB
miami_osm.db .......... 95.8 MB
nodes.csv ............. 63.2 MB
nodes_tags.csv ........ 2.6 MB
ways.csv .............. 6.4 MB
ways_tags.csv ......... 16.8 MB
ways_nodes.cv ......... 19.6 MB  
```  

### Number of Unique Users
```SQL
select count(subq.uid)
FROM (select uid
from ways
UNION
select uid
from nodes)as subq;
```
749
### Number of Nodes
```SQL
select count(*)
from nodes;
```
699776
### Number of Ways
```SQL
select count(*)
from ways;
```
96949
### Number of Schools
```SQL
select count(*) as total
from nodes_tags 
where value='school';
```
635
### Foodies
Users with the most restaurant submissions
```SQL
select user, count(*) as total 
from nodes join nodes_tags 
on nodes.id=nodes_tags.id 
where value='restaurant' 
group by user 
order by total desc limit 10;
```
```SQL
"Quyen Tran",48
wegavision,20
IvoSan,19
SpikeJ,13
igfc,13
ErnieAtLYD,10
Extrabrandt,10
thetornado76,8
GoWestTravel,7
juanpinillos,7
```
The top 10 contributers of restaurant data accounted for 75% of the entries.

### Roadsters
Users with most highway data submissions
```SQL
select user, count(*) as total 
from ways join ways_tags 
on ways.id=ways_tags.id 
where key='highway' 
group by user 
order by total desc limit 10;
```
```SQL
bot-mode,8910
carciofo,4795
grouper,2902
NE2,1082
IvoSan,1071
georafa,741
Trex2001,739
dufekin,502
DaveHansenTiger,355
maxolasersquad,346
```
The top 10 contributers accounted for 75% of the entries.

### Other Ideas
The OSM website imports part of its data from the United States Census Bureau. It seems like there are issues in the formatting of the zipcodes from this data. This can be seen below:
```SQL
SELECT tags.type, tags.value,  COUNT(*) as count 
FROM (SELECT * FROM nodes_tags 
	  UNION ALL 
      SELECT * FROM ways_tags) tags
WHERE tags.key='zip_left' or tags.key='zip_right'
GROUP BY tags.value
ORDER BY count DESC;
```
```SQL
tiger,33010:33142,48
tiger,33147:33150,32
tiger,33150:33168,24
tiger,33133:33134:33135,20
tiger,33133:33135:33145,18
tiger,33176:33186,16
tiger,33176:33186;33176,15
tiger,"33172; 33178",14
tiger,33012:33166,12
tiger,33126:33172;33172,12
tiger,"33155:33158:33158; 33143; 33158",12
tiger,"33155:33158; 33143; 33158",12
```
It seems like this data needs to be cleaned more thoughouly prior to posting onto the OSM site. One solution is to read through all of the tiger values and split based on given string length. Anything after the fifth character would be dropped in this case. The query above shows entries that have various zipcodes under the same tag. In this case, the data would need to be cross referenced to ensure that the resulting entry is accurate.

 OpenStreetMap Data Case Study

### Map Area
Miami,Florida, United States

- [https://www.openstreetmap.org/#map=12/25.7588/-80.2180](https://www.openstreetmap.org/#map=12/25.7588/-80.2180)

This is a map of my hometown from an open source mapping site called OpenStreetMap. Users are able to contribute to the map as they see fit. Given that it is a collaborative map, it is especially prone to human error. I would like to access the quality of the data for this subsect and determine if there are any necessary changes.

## Initial Inspection
#### Boundary

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
#### Street Names

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

"INSERT HERE"
 
#### Cardinal Directions
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

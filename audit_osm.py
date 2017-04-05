#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 28 21:57:06 2017

@author: jorge
"""


import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow
import pprint
import re
from collections import defaultdict

osm_file = "Sample.osm"  # Replace this with your osm file

def count_tags(filename):
    "Returns a dictionary with tag types and number of occurances"
    tag_count={}
    for event, elem in ET.iterparse(filename, events=('start',)):
        if elem.tag in tag_count:
            tag_count[elem.tag]=tag_count[elem.tag]+1
        else:
            tag_count[elem.tag]=1
    
    return tag_count
    


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    """
Checks the "k" value for each "<tag>" and see if there are any potential problems.
We have provided you with 3 regular expressions to check for certain patterns
in the tags. We would like to change the data model and expand the "addr:street" 
type of keys to a dictionary like this:{"address": {"street": "Some value"}}
So, we have to see if we have such tags, and if we have any tags with
problematic characters.

The function 'key_type', returns a count of each of
four tag categories in a dictionary:
  "lower", for tags that contain only lowercase letters and are valid,
  "lower_colon", for otherwise valid tags with a colon in their names,
  "problemchars", for tags with problematic characters, and
  "other", for other tags that do not fall into the other three categories.
"""

    
    if element.tag == "tag":
        for tag in element.iter("tag"):
            try:
                lo=lower.search(element.attrib['k'])
                if lo:
                    keys['lower']+=1
                    return keys
                loc=lower_colon.search(element.attrib['k'])
                if loc:
                    keys['lower_colon']+=1
                    return keys
                prob=problemchars.search(element.attrib['k'])
                if prob:
                    keys['problemchars']+=1
                    return keys
                else:
                    #print element.attrib['k']
                    keys['other']+=1
                    return keys
            except:
                pass
    return keys
         
            

def process_map(filename):
    """Iteratively parse through file and determine which keys are lower,lower_colon,
    problemchars, or other type. These are the descriptions of each category:
   "lower", for tags that contain only lowercase letters and are valid,
   "lower_colon", for otherwise valid tags with a colon in their names,
   "problemchars", for tags with problematic characters, and
   "other", for other tags that do not fall into the other three categories.
    
   Returns a dictionary with tag types and number of occurances
        """
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    
    return keys
    




def get_user(tag):
    """Check for user"""
    return tag.attrib['user']


def process_users(filename):
    """Returns a list of unique users that contributed to file"""
    users = set()
    for _, element in ET.iterparse(filename):
        for tag in element:
            try:
                u=get_user(tag)
                if u !=None:
                    users.add(u)
            except:
                pass
    return users



#Improving Street Names

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Ave.": "Avenue",
            
            }


def audit_street_type(street_types, street_name):
     """The street type of street_name input is checked against expected list. This contains
    the intended street type naming conventions for data standardization """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
    return street_types


def is_street_name(elem):
    """Check to see if k attribute value of element is a street name"""
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    """Iteratively parse file and return a dictionary of unique street values
    that do not match expected list along with a list of their occurances"""
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types.keys()
    


def update_name(name, mapping):
    "Match the current street type with mapping list and return standardized value"
    m=street_type_re.search(name)
    name=name[:len(name)-len(m.group())]+mapping[m.group()]
    print name

    return name
    
    
def test():
    st_types = audit(OSMFILE)
    assert len(st_types) == 3
    pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping)


def map_boundary(filename):
    """Find the max/min values for latitude and longitude from map data.
      These are the boundaries of the extract."""
    for _, element in ET.iterparse(filename):
        if element.tag == "bounds":
            minlat=float(element.attrib['minlat'])
            minlon=float(element.attrib['minlon'])
            maxlat=float(element.attrib['maxlat'])
            maxlon=float(element.attrib['maxlon'])
            #print y['minlat']
            return minlat,minlon,maxlat,maxlon
            
def boundary_check(filename):
    """Check if all nodes lie within the boundaries of the map"""
    errors={'wrong_coordinates':0}
    minlat,minlon,maxlat,maxlon=25.6692244, -80.4231834, 25.87093, -80.115347
    for _, element in ET.iterparse(filename):
        if element.tag == "node":
            if (element.attrib['lat']<minlat) or (element.attrib['lat']>maxlat):
                errors['wrong_coordinates']+=1
            elif (element.attrib['lon']<minlon) or (element.attrib['lon']>maxlon):
                errors['wrong_coordinates']+=1
    return errors


    
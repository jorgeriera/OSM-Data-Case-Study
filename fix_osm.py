#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  2 18:56:48 2017

@author: jorge
"""

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
from collections import OrderedDict

import cerberus

import schema

OSM_PATH = "Sample.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_extra_space_re=re.compile( '\s+', re.IGNORECASE)


direction=['Southwest','Southeast','Northwest','Northeast', 'North','South','East','West']
abbv_direction=['N.W.','N.E.','S.E.','S.W.','NW','NE','SW','SE','N','S','W','E','N.','S.','E.','W.']
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
            
            
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

def audit_street_type(street_name,mapping): 
    """The street type of street_name input is checked against expected list. This contains
   the intended street type naming conventions for data standardization """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_name=update_name(street_name,mapping)
    return street_name

            
def is_street_name(elem):
    "Check to see if k attribute value of element is a street name"
    return (elem.attrib['k'] == "addr:street")


def update_name(name, mapping):
    "Match the current street type with mapping list and return standardized value"
    m=street_type_re.search(name)
    if m.group() in mapping.keys():
        name=name[:len(name)-len(m.group())]+mapping[m.group()]
    return name
    
def update_direction(name,mapping):
    "Match the cardinal direction with mapping list and return standardized value"
    name_val=name.attrib['v']
    abbv=name.attrib['v'].split(' ')[0]
    name=mapping[abbv]+name_val[len(abbv):]
    return name


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    #Standardize street names and cardinal directions
    for tag in element.iter("tag"):
        if is_street_name(tag) and (tag.attrib['v'].split(' ')[0] in abbv_direction):
            tag.attrib['v']=update_direction(tag,direction_mapping)
            tag.attrib['v']=audit_street_type(tag.attrib['v'], mapping)

    
    if element.tag == 'node':
        for attribute in element.attrib:
            if attribute in NODE_FIELDS:
                node_attribs[attribute]=element.attrib[attribute]
        
        sub_iter=element.iter("tag")
        for atr in sub_iter:
            k_val=atr.attrib['k']
            locol=LOWER_COLON.search(k_val)
            prochar=PROBLEMCHARS.search(k_val)
            if locol:
                key_list = k_val.split(':',1)
                k_key=key_list[1]
                tag_type=key_list[0]
            elif prochar:
                break
            else:
                tag_type="regular"
                k_key=k_val
            v_val=atr.attrib['v']
            content={"id":node_attribs['id'],'key':k_key,'value':v_val,'type':tag_type}
            tags.append(content)
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        for attribute in element.attrib:
            if attribute in WAY_FIELDS:
                way_attribs[attribute]=element.attrib[attribute]

        sub_iter=element.iter("nd")
        level=0
        for atr in sub_iter:
            for sub_attrib in atr.attrib:
                if sub_attrib=='ref':
                    content= {"id":way_attribs['id'],'node_id':atr.attrib[sub_attrib],'position':level}
                    way_nodes.append(content)
                    level+=1
        sub_iter=element.iter("tag")
        for atr in sub_iter:
            k_val=atr.attrib['k']
            locol=LOWER_COLON.search(k_val)
            prochar=PROBLEMCHARS.search(k_val)
            if locol:
                key_list = k_val.split(':',1)
                k_key=key_list[1]
                tag_type=key_list[0]
            elif prochar:
                break
            else:
                tag_type="regular"
                k_key=k_val
            v_val=atr.attrib['v']
            content={"id":way_attribs['id'],'key':k_key,'value':v_val,'type':tag_type}
            tags.append(content)            
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

        


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                    
                    
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
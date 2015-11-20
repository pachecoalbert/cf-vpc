#!/usr/bin/python
"""
# -----------------------------------------------------------------------------

File name: get_cfn_output.py
Date created:  January 30, 2015
Created by: Al Pacheco

Program Description:  ToDo

Program Requirements
##  Requirement
------  ----------------------------------------------------------------------


Revisions:
Date            Revised by                        Comments
----------  ----------------          -----------------------------------------------
20150130    Al Pacheco                      Script Created

# -----------------------------------------------------------------------------
"""

# Import Python modules
import boto
import sys
import os
import subprocess
import yaml

# Import custom modules
from cfn_module import *


# -----------------------------------------------------------------------------
#                                                           FUNCTIONS
# -----------------------------------------------------------------------------






# -----------------------------------------------------------------------------
#                                                           MAIN
# -----------------------------------------------------------------------------

# Check to if required arguments have been provided
if len(sys.argv) < 2 :
    print 'Usage: ', sys.argv[0], ' <stack_name> '
    print'\t <stack_name> = Specify name of cfn stack.'
    print'\t <aws_profile> = Specify aws profile.'
    exit(1)


# Debug argv
"""
argv_len = len(sys.argv)
for arg in  sys.argv:
    print "Value of argv = %s" % arg
#    print "Index %s: , Value: %s" % i, sys.argv[i]
"""

# >>>> BEGIN >>>>>>>>>>>>
# >>>> VARIABLE DECLARATIONS

BASE_PATH = '/u01/ro-poc/'
BINDIR = BASE_PATH+'bin/'
DATDIR = BASE_PATH+'dat/'

# Create session ball dictionary
session_ball = {};

# Setup  variables
session_ball['stack_name'] =  sys.argv[1]
session_ball['aws_profile'] = sys.argv[2]
session_ball['CFN_REGION'] = 'us-east-1'


# Establish cfn connection
#print "\t Establishing CFN connectin....",
cfn_conn = initiate_cfn_connection(session_ball['CFN_REGION'],session_ball['aws_profile'] )
#print "Done!"

# Retrive stack object
try:
    stack = cfn_conn.describe_stacks(session_ball['stack_name'] )
except Exception, e:
    print "\t Unable to retrieve CFN Stack object. ERROR %s" % e

# Define yaml doc variable
yaml_doc = {}

# Retrieve stack ouputs and place into an array
for output in stack[0].outputs:
    #print('%s=%s (%s)' % (output.key, output.value, output.description))
    # Create array to hold list of raw itmes
    values = []
    # Create array to hold list of translated items
    values_trans = []

    # Check if stack output value is a LIST
    if output.description.find('LIST') >0:
        values = output.value.split(",")
        # Loop through values and convert raw string value to translated value
        for z, value in enumerate(values):
            for output2 in stack[0].outputs:
                if output2.key == value:
                    #print  'Key = {}: Value = {}'.format(value,output2.value)
                    values_trans.append(output2.value)
        element = {output.key: values_trans}
    else:
        # Output a NOT a list so just grab stack output variable
        element = {output.key: output.value}

    # Build the yaml docuent
    yaml_doc.update(element)
print yaml.safe_dump(yaml_doc, default_flow_style=False)

#print yaml_doc.keys()

exit(0)



'''
************** TEST CODE *************
test_dict = {'key': 'Value'}
test_dict.update({'key2':'Value2'})
test_dict.update({'key3':['item1','item2']})
print yaml.safe_dump(test_dict, default_flow_style=False)
exit(0)

'''

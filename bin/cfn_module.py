#!/usr/bin/python
"""
# -----------------------------------------------------------------------------

File name: cfn_module.py
Date created: January 30, 2015
Created by: Al Pacheco

Usage: This is a Python Module for CFN

Program Description: To Do


Revisions:
Date            Revised by                        Comments
----------  ----------------          -----------------------------------------------
20150130   Al Pacheco                      Script Created

# -----------------------------------------------------------------------------
"""

# Import Python modules
import boto
import sys
import os
import boto.cloudformation
from boto.sqs.message import Message
#import subprocess

# -----------------------------------------------------------------------------
#                                                           FUNCTIONS
# -----------------------------------------------------------------------------

def initiate_cfn_connection(aws_region,profile=None):
    # Create a connection to AWS SQS
    try:
        if profile is not None:
            cfn_conn = boto.cloudformation.connect_to_region(aws_region,profile_name=profile)
        else:
            cfn_conn = boto.cloudformation.connect_to_region(aws_region)

    except Exception, e:
        print "\t Unable to establish CFN Connection. ERROR %s" % e
        exit(1)
    return cfn_conn

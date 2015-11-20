#!/usr/bin/python


# Import Python modules
import sys
from cfn_pyplates.core import *
import pprint

# Import custom modules
# If our base template isn't on the PYTHONPATH already, we need to do this:
sys.path.append('./')

# NOTE
# Naming standards for cloud resoruces are described at: https://confluence.huit.harvard.edu/pages/viewpage.action?title=%5BSTANDARD%5D+-+Cloud+Resource+Naming+Conventions&spaceKey=CLOPS

# -----------------------------------------------------------------------------
#                                                           FUNCTIONS
# -----------------------------------------------------------------------------

#NOTE - Need to push the next 2 functions into a module
# This function will generate a cfn Output Resource - Strning type
def create_output_resource_str(out_name,out_value,out_descr):
    cft.outputs.add(Output('{}'.format(out_name),
        '{}'.format(out_value) ,
        '{}'.format(out_descr))
    )

# This function will generate a cfn Output Resource - Ref type
def create_output_resource_ref(out_name,out_value,out_descr):
    cft.outputs.add(Output('{}'.format(out_name),
        ref('{}'.format(out_value)),
        '{}'.format(out_descr))
    )

# Appends a Name Tag to the default cfn tags
def append_name_tag_to_default(tag_value):
    # Build tags
    default_tags = []

    for key, value in options['tags'].iteritems():
      #print 'key = ', key
      #print 'value = ', value

      t = {'Key': key,
            'Value': value}
      default_tags.append(t)

    name_tag = {'Value': tag_value, 'Key': 'Name'}
    default_tags.append(name_tag)
    return default_tags

# -----------------------------------------------------------------------------
#                                                           MAIN
# -----------------------------------------------------------------------------

pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(options['tags'])

# Setup App and Account Name Constructs
account_name_construct ='{}-{}-{}'.format(options['group'],options['tags']['environment'],options['context'])
appname_construct = '{}-{}'.format(options['appName'],options['tags']['environment'])

# Pull region number
region_num = options['Region'][-1:]

# Create cft object with stack description
description = '{0} NAT stack'.format(account_name_construct)
cft = CloudFormationTemplate(description)

# Create default output  resources
create_output_resource_str('environment',options['tags']['environment'],'environment')
create_output_resource_str('huitAssetid',options['tags']['huit_assetid'],'huit_assetid')
create_output_resource_str('lastmodifiedby',options['tags']['lastmodifiedby'],'lastmodifiedby')
create_output_resource_str('product',options['tags']['product'],'product')
create_output_resource_str('Region',options['Region'],'Region')

# NAT server iam instance role
nat_iam_role_tag_name =  '{0}{1}'.format(appname_construct,'-instance-iam-role')
nat_iam_role_resource_name = nat_iam_role_tag_name.replace("-", "")
#tags = append_name_tag_to_default(nat_iam_role_tag_name)
cft.resources.add(Resource(nat_iam_role_resource_name,
                           'AWS::IAM::Role',
                           {
                               'AssumeRolePolicyDocument': {
                                   'Statement': [
                                       {
                                           'Effect': 'Allow',
                                           'Principal': {
                                               'Service': [
                                                   'ec2.amazonaws.com'
                                               ]
                                           },
                                           'Action': 'sts:AssumeRole'
                                       }
                                   ]
                               },
                               'Path': '/'
                           })
                  )
# Generate CFN Outoputs
create_output_resource_ref('NatIamRole', nat_iam_role_resource_name,'IAM  Role ID.')

# NAT Instance role policies
nat_iam_role_policy_tag_name =  '{0}{1}'.format(appname_construct,'-instance-iam-policy')
nat_iam_role_policy_resource_name = nat_iam_role_policy_tag_name.replace("-", "")
#tags = append_name_tag_to_default(nat_iam_role_policy_tag_name)
cft.resources.add(Resource(nat_iam_role_policy_resource_name,
                           'AWS::IAM::Policy',
                           {
                               'PolicyName': 'NatInstanceRole',
                               'PolicyDocument': {
                                   'Statement': [
                                       {
                                           'Effect': 'Allow',
                                           'Action': [
                                               'ec2:DescribeInstances*',
                                               'ec2:CreateRoute*',
                                               'ec2:ReplaceRoute',
                                               'ec2:StartInstances'
                                           ],
                                           'Resource': '*'
                                       },
                                       {
                                           'Effect': 'Allow',
                                           'Action': [
                                               'logs:*'
                                           ],
                                           'Resource': 'arn:aws:logs:*:*:*'
                                       }
                                   ]
                               },
                               'Roles': [
                                   ref('{}'.format(nat_iam_role_resource_name))
                               ]
                           })
                  )
# Generate CFN Outoputs
create_output_resource_ref('NatIamPolicy', nat_iam_role_policy_resource_name,'IAM Policy ID.')


# NAT Instance profile
nat_iam_profile_tag_name =  '{0}{1}'.format(appname_construct,'-instance-profile')
nat_iam_profile_resource_name = nat_iam_profile_tag_name.replace("-", "")
#tags = append_name_tag_to_default(nat_iam_profile_tag_name)

cft.resources.add(Resource(nat_iam_profile_resource_name,
                           'AWS::IAM::InstanceProfile',
                           {
                               'Path': '/',
                               'Roles': [
                                   ref('{}'.format(nat_iam_role_resource_name))
                               ]
                           })
                  )

# Generate CFN Outoputs
create_output_resource_ref('NatInstanceProfile', nat_iam_profile_resource_name,'IAM Profile ID.')


# Security Group for Nat Server instances
security_group_tag_name =  '{0}{1}'.format(appname_construct,'-management-sg')
security_group_resource_name = security_group_tag_name.replace("-", "")
tags = append_name_tag_to_default(security_group_tag_name)
cft.resources.add(Resource(security_group_resource_name,
                           'AWS::EC2::SecurityGroup',
                           {
                               'GroupDescription': 'allows traffic to the app server instances',
                               'VpcId': options['VpcId'],
                               'SecurityGroupIngress': [{
                                   'IpProtocol': 'tcp',
                                   'FromPort': 0,
                                   'ToPort': 65535,
                                   "CidrIp": options['VpcCidr']
                               }
                               ],
                               "Tags": tags
                           }
                           )
                  )
# Generate CFN Outoputs
create_output_resource_ref('NatSecurityGroup', security_group_resource_name,'Security Group ID.')

# Define the subnets to be used by the NAT instances
azs = options['AZs']

# Loop for each AZ
for i, az in enumerate(azs):

  # Create resource name
  nat_tag_name = '{0}{1}{2}{3}'.format(appname_construct,'-nat-',region_num,az)
  nat_resource_name = nat_tag_name.replace("-", "")
  tags = append_name_tag_to_default(nat_tag_name)

  # Grab the network for this AZ
  NatNet = options['elbpublic{}'.format(az.upper())]

  properties = {
      'ImageId':   options['NatRegionImageID'],
      "IamInstanceProfile" : {"Ref":'{}'.format(nat_iam_profile_resource_name)},
      'InstanceType': options['NATInstanceType'],
      "SourceDestCheck": "false",
      "Tags": tags,
       "NetworkInterfaces": [
          {
            "GroupSet": [
              {
                "Ref": "{}".format(security_group_resource_name)
              }
            ],
            "AssociatePublicIpAddress": "true",
            "DeviceIndex": "0",
            "DeleteOnTermination": "true",
            "SubnetId": NatNet
          }
        ]
  }

  # Add NAT instance resource
  cft.resources.add(
      Resource(nat_resource_name, 'AWS::EC2::Instance', properties,)
  )
  # Generate CFN Outoputs
  create_output_resource_ref(nat_resource_name, nat_resource_name,'Instance ID.')

  # Add internal route
  rout = 'InternalRoute{}'.format(az.upper())
  route_table_name = 'PrivateRouteTable{}'.format(az.upper())
  route_table_resoruce = options[route_table_name]
  cft.resources.add(Resource(rout,
                             'AWS::EC2::Route',
                             {
                               'DestinationCidrBlock' : '0.0.0.0/0',
                               'InstanceId' : ref('{}'.format(nat_resource_name)),
                               'RouteTableId' : route_table_resoruce,
                             })
                   )


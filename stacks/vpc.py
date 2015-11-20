#!/usr/bin/python

# Import Python modules
import sys
from cfn_pyplates.core import Resource
from netaddr import IPNetwork
import pprint

# Import custom modules
# If our base template isn't on the PYTHONPATH already, we need to do this:
sys.path.append('./')

# NOTE
# Naming standards for cloud resoruces are described at: https://confluence.huit.harvard.edu/pages/viewpage.action?title=%5BSTANDARD%5D+-+Cloud+Resource+Naming+Conventions&spaceKey=CLOPS

# -----------------------------------------------------------------------------
#                                                           FUNCTIONS
# -----------------------------------------------------------------------------

# This function will generate a cfn Output Resource - String type
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

# Create cft object with stack description
description = '{0} VPC stack'.format(account_name_construct)
cft = CloudFormationTemplate(description)

# Create default output  resources
create_output_resource_str('environment',options['tags']['environment'],'environment')
create_output_resource_str('huitAssetid',options['tags']['huit_assetid'],'huit_assetid')
create_output_resource_str('lastmodifiedby',options['tags']['lastmodifiedby'],'lastmodifiedby')
create_output_resource_str('product',options['tags']['product'],'product')
create_output_resource_str('Region',options['Region'],'Region')
create_output_resource_str('CIDR',options['CIDR'],'CIDR')




#create_output_resource_str('PubKey',options['PubKey'],'PubKey')
#

# Define the VPC subpernet and create an array of subnets.
network = IPNetwork(options['CIDR'])
subnets = []
for subnet in network.subnet(24):
  subnets.append(subnet)

# Define the subnetts that will be used in this VPC
elb_public_subnets = subnets[0:4]
elb_private_subnets  = subnets[4:8]
apps_private_subnets =  subnets[8:12]
db_subnets =  subnets[12:16]

# Create list of AZ's
azs = ['a','c', 'd','e']

# Place VPC subnets into an dict for processing
# the dict key is used  to construct the subnet name
# The array[0] is used to determine which route table to accosiate the subnet to.
# The array[1] holds the array of subnets for the subnet type (key)
vpc_subnets_dict = {
  'elb-public': ['pub',elb_public_subnets],
  'elb-private': ['priv',elb_private_subnets],
  'app-private': ['priv',apps_private_subnets],
  'db-private': ['priv',db_subnets]
}
region_num = options['Region'][-1:]

# Creat the VPC
vpc_resource_name = '{0}'.format(account_name_construct)
tags = append_name_tag_to_default(vpc_resource_name)
cft.resources.add(Resource('VPC',
                           'AWS::EC2::VPC',
                           {
                             'CidrBlock': '{}'.format(network.cidr),
                             'InstanceTenancy': 'default',
                             'EnableDnsSupport': 'true',
                             'EnableDnsHostnames': 'true',
                             'Tags': tags
                           })
                  )

# Generate CFN Outoputs
create_output_resource_ref('VpcId', 'VPC','VPC ID of new / updated VPC.')
create_output_resource_str('VpcCidr', '{}'.format(network.cidr),'VPC CIDR.')


# Create the Internet Gateway
tags = append_name_tag_to_default('InternetGateway')
cft.resources.add(Resource('InternetGateway',
                           'AWS::EC2::InternetGateway',
                           {
                              #No Properties
                           })
                 )

# Generate CFN Outoputs
create_output_resource_ref('InternetGateway', 'InternetGateway','InternetGateway ID .')

# Attach the Internet Gateway to the VPC
cft.resources.add(Resource('InternetGatewayAttachment',
                           'AWS::EC2::VPCGatewayAttachment',
                           {
                             'InternetGatewayId' : ref('InternetGateway'),
                             'VpcId' : ref('VPC')
                           })
                 )



# Create variables for Loop to create internal route tables
internal_route_tables = {}
output_value = []
output_name = ''

# Create internal route tables
for num in range(1, 5):
  # assign az avlue.  Subtract 1 to reflect for loop start at postion 1
  az = azs[num-1]

  # Create resource and tag names
  #print 'num == ', num
  internal_route_tag_name =  '{0}{1}{2}{3}{4}{5}'.format(account_name_construct,'-','private-','rt-',region_num,az)
  internal_route_resource_name = internal_route_tag_name.replace("-", "")
  #print 'internal_route_resource_name = ', internal_route_resource_name

  internal_route_tables[az] = internal_route_resource_name
  tags = append_name_tag_to_default(internal_route_tag_name)
  cft.resources.add(Resource(internal_route_resource_name,
                           'AWS::EC2::RouteTable',
                           {
                             'VpcId': ref('VPC'),
                             'Tags': tags
                           })
                 )
  # Generate CFN Outoputs
  create_output_resource_ref('PrivateRouteTable{}'.format(az.upper()), internal_route_resource_name,'Internal Route Table ID .')
  output_value.append('PrivateRouteTable{}'.format(az.upper()))



output_name = 'PrivatRouteTables'
# Generate CFN Outoputt for AZ Lists
create_output_resource_str(output_name, ','. join(output_value), '[LIST] {} Names'.format(output_name))


# Create the Public Route table
external_route_tag_name =  '{0}{1}{2}'.format(account_name_construct,'-public-','rt')
external_route_resource_name = external_route_tag_name.replace("-", "")
tags = append_name_tag_to_default(external_route_tag_name)
cft.resources.add(Resource(external_route_resource_name,
                           'AWS::EC2::RouteTable',
                           {
                             'VpcId': ref('VPC'),
                             'Tags': tags
                           })
                 )
# Generate CFN Outoputs
create_output_resource_ref('PublicRouteTable', external_route_resource_name,'External Route Table ID .')

# Create the Pub subnet route to the Internet
pub_route_internet_name = 'ExternalRoute'
cft.resources.add(Resource(pub_route_internet_name,
                           'AWS::EC2::Route',
                           {
                             'DestinationCidrBlock' : '0.0.0.0/0',
                             'GatewayId' : ref('InternetGateway'),
                             'RouteTableId' : ref('{}'.format(external_route_resource_name)),
                           })
                 )

# Create the DHCP Option group using AWS internal Domain Names and DNS
cft.resources.add(Resource('DHCPOptions',
                           'AWS::EC2::DHCPOptions',
                           {
                              'DomainName': 'ec2.internal',
                              'DomainNameServers': ['AmazonProvidedDNS']
                           })
                 )

# Create Network ACL for VPC
cft.resources.add(Resource('NetworkAcl',
                           'AWS::EC2::NetworkAcl',
                           {
                             'VpcId': ref('VPC')
                           })
                 )

# Create default network ACL allowing ALL Ingress
cft.resources.add(Resource('NetworkAclEntryIngress',
                           'AWS::EC2::NetworkAclEntry',
                           {
                             'CidrBlock' : '0.0.0.0/0',
                             'Egress' : False,
                             'NetworkAclId' : ref('NetworkAcl'),
                             'Protocol' : -1,
                             'RuleAction' : 'allow',
                             'RuleNumber' : 100
                           })
                 )

# Create default network ACL allowing ALL Egress
cft.resources.add(Resource('NetworkAclEntryEgress',
                           'AWS::EC2::NetworkAclEntry',
                           {
                             'CidrBlock' : '0.0.0.0/0',
                             'Egress' : True,
                             'NetworkAclId' : ref('NetworkAcl'),
                             'Protocol' : -1,
                             'RuleAction' : 'allow',
                             'RuleNumber' : 100
                           })
                 )

# Setup variables with null
# These are used to aggregate LITS output data
output_value = []
output_name = ''

# Generate AZ cfn outputs
for i, az in enumerate(azs):
    az_resource_name = 'az{}'.format(az.upper())
    # Generate CFN Outoputs
    cft.outputs.add(Output(az_resource_name,
        az,
        '{} AZ ID'.format(az_resource_name))
    )
    output_value.append(az_resource_name)

output_name = 'AZs'
# Generate CFN Outoputt for AZ Lists
create_output_resource_str(output_name, ','. join(output_value), '[LIST] {} Names'.format(output_name))



# Loop for each VPC Tier
#for x, tier_subnets in enumerate(vpc_subnets):

# Set a counter that will be used in the next loop
x = 0

for subnet_name, subnet_list  in vpc_subnets_dict.iteritems():
  output_value = []
  output_name = ''

  # Capture the subnet type [public | private]
  subnet_type = subnet_list[0]

  # Create subnet for each network tier
  for i, subnet in enumerate(subnet_list[1]):
    az = azs[i]

    tags = []
    subnet_tag_name = '{0}{1}{2}{3}{4}{5}{6}'.format(account_name_construct,'-', subnet_name,'-',region_num,az,'-1')
    subnet_resource_name = subnet_tag_name.replace("-", "")
    tags = append_name_tag_to_default(subnet_tag_name)
    cft.resources.add(Resource(subnet_resource_name,
                               'AWS::EC2::Subnet',
                               {
                                 'CidrBlock': '{}'.format(subnet.cidr),
                                 'AvailabilityZone': '{}{}'.format(options['Region'],az),
                                 'VpcId': ref('VPC'),
                                 'Tags': tags
                               })
                     )

    # Determine appropriate route table and associate to subnet
    if subnet_type  == 'pub':
        route_assoc_resource_name = '{}SubnetRouteAssociation{}'.format(subnet_name,az.upper()).replace("-", "")
        route_table = external_route_resource_name

        cft.resources.add(Resource(route_assoc_resource_name,
                                   'AWS::EC2::SubnetRouteTableAssociation',
                                   {
                                     'RouteTableId': ref('{}'.format(route_table)),
                                     'SubnetId': ref(subnet_resource_name)
                                   })
                         )

    # Will NOT be associateing the private subnetts now.  Will do  with Nat stack
    else:
        route_assoc_resource_name = '{}SubnetRouteAssociation{}'.format(subnet_name,az.upper()).replace("-", "")
        route_table = internal_route_tables[az]
        cft.resources.add(Resource(route_assoc_resource_name,
                               'AWS::EC2::SubnetRouteTableAssociation',
                               {
                                 'RouteTableId': ref('{}'.format(route_table)),
                                 'SubnetId': ref(subnet_resource_name)
                               })
                     )



    # Generate CFN Outoputs
    subnet_resrouce_name = '{}{}'.format(subnet_name.replace("-", ""),az.upper())
    create_output_resource_ref(subnet_resrouce_name, subnet_resource_name, '{} Subnet ID'.format(subnet_resource_name))
    output_value.append(subnet_resrouce_name)


  output_name = '{}Subnets'.format(subnet_name).replace("-", "")
  # Generate CFN Outoputt for Subnet Lists
  create_output_resource_str(output_name, ','. join(output_value),'[LIST] {} Names'.format(output_name))

  # Increment the counter for the outter loop
  x += 1



# cf-vpc

### VPC
- Generate cloud formation jason template

cd into the repo directory
```
cd ./cf-vpc/
```

Generate the cloud formation template via cfn pyplates
```
cfn_py_generate ./stacks/vpc.py vpc-stack.json -o ./mappings/vpc.yaml 
```

- Create the vpc stack
Issue the aws cli command to create the vpc stack.  (Be sure to use the correct --profile)
```
 aws --region us-east-1 --profile cloudhacks cloudformation create-stack --stack-name admints-dev-standard-vpc --template-body  file://vpc-stack.json
```

### NAT (for above VPC)

- Retrive output variable and gernate yaml mapings
Cd into the report directoy
```
cd ./cf-vpc/
```
Pull the nat stack yaml parameters into a new mapping file. (this will overwriete the original file if exists)
```
cat ./mappings/nat.yaml > ./temp/nat_aggr.yaml
```

Pull the Prereq VPC stack output parameters into the new mapping file
```
./bin/get_cfn_output.py admints-dev-standard-vpc cloudhacks >> ./temp/nat_aggr.yaml
```
- Generate cloud formation jason template

Cd into the report directoy
```
cd ./cf-vpc/
```

Generate the cloud formation template via cfn pyplates
```
cfn_py_generate ./stacks/vpc.py vpc-stack.json -o ./mappings/vpc.yaml 
```

- Create the vpc stack
Issue the aws cli command to create the vpc stack.  (Be sure to use the correct --profile)
```
aws --region us-east-1 --profile cloudhacks cloudformation create-stack --stack-name admints-dev-standard-nat --template-body  file://nat-stack.json --capabilities CAPABILITY_IAM
```

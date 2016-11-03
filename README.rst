OpenStack Resources Collector For CIS
=====================================


.. image:: https://coveralls.io/repos/github/seecloud/cis-collector-openstack/badge.svg?branch=development
    :target: https://coveralls.io/github/seecloud/cis-collector-openstack?branch=development

.. image:: https://travis-ci.org/seecloud/cis-collector-openstack.svg?branch=development
    :target: https://travis-ci.org/seecloud/cis-collector-openstack

# CIS OpenStack Collector
CIS OpenStack collector monitors OpenStack components (e.g. nova, keystone, neutron) and tracks all changes in those components resources (e.g. projects in keystone, servers in nova, snapshots in cinder)

#### Components
* cis-openstack-collector
* cis-server
Both components are running in docker containers


#### Requirements
1. OpenStack >=8.0
2. Host with docker>=1.8 and access to OpenStack controller management network

#### How to run?

1. Clone repository to your docker host
```
git clone git@github.com:seecloud/cis-collector-openstack.git
```
2. Open collector folder
```
cd cis-collector-openstack
```
3. Configure environment variables in *oscollector-env* file
```
OS_USERNAME=admin
OS_PASSWORD=msa
OS_TENANT_NAME=admin
OS_CONTROLLER_IP=172.18.128.104
OS_USER_DOMAIN_ID=default
OS_PROJECT_DOMAIN_ID=default
OS_REGION_NAME=default

# CIS_SERVER address - do not change
# This value is used for running docker with --link option
CIS_SERVER=cis-server

```

4. Run deployment with *run.sh* script
```
chmod +x run.sh
./run.sh
```

Example of running deployment
```
- Init application variables
- Check if docker is installed...
- Building CIS-server docker image...
- Building CIS-openstack-collector docker image...
- Create  cis network for application
  Make sure, that 172.19.0.0/16 network is allowed on OpenStack controller
- Remove previously runned cis-server application
- Running cis-server application...
  You can follow application logs by running 'docker logs -f cis-server'
- Remove previously runned cis-os-collector application
- Running cis-os-collector application and link it to cis-server hostname
  You can follow application logs by running 'docker logs -f cis-os-collector'
- Add cis-server to cis network
- Add cis-os-collector to cis network

- Application deployment finished.
```

#### Issues
Report if you have found some
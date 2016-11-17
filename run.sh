#!/bin/bash

echo "- Init application variables"
source oscollector-env
CIS_SERVER_IMAGE="cis-server"
CIS_OS_COLLECTOR_IMAGE="cis-os-collector"
CIS_SERVER_APP="cis-server"
CIS_OS_COLLECTOR_APP="cis-os-collector"

CIS_CONTAINER_NETWORK=cis

# check if docker installed
echo "- Check if docker is installed..."
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but it's not installed.  Aborting."; exit 1; }


# Build cis-server image
echo "- Building CIS-server docker image..."
cd cis-server
docker build -t ${CIS_SERVER_IMAGE} . > /dev/null

# Build cis-collector image
cd ..
echo "- Building CIS-openstack-collector docker image..."
docker build -t ${CIS_OS_COLLECTOR_IMAGE} -f Dockerfile . > /dev/null

# Create network for containers
docker network ls | grep ${CIS_CONTAINER_NETWORK} > /dev/null
if [ $? -eq 0 ]; then
    docker network disconnect ${CIS_CONTAINER_NETWORK} ${CIS_SERVER_APP} 2> /dev/null
    docker network disconnect ${CIS_CONTAINER_NETWORK} ${CIS_OS_COLLECTOR_APP} 2> /dev/null
    docker network rm ${CIS_CONTAINER_NETWORK} > /dev/null
fi
echo "- Create  ${CIS_CONTAINER_NETWORK} network for application"
docker network create ${CIS_CONTAINER_NETWORK} > /dev/null
address=$(docker network inspect cis | grep Subnet | cut -d '"' -f 4)
echo "  Make sure, that ${address} network is allowed on OpenStack controller"

# Remove currently running cis-server
docker ps -a | grep ${CIS_SERVER_APP} > /dev/null
if [ $? -eq 0 ]; then
    echo "- Remove previously runned ${CIS_SERVER_APP} application"
    docker rm ${CIS_SERVER_APP} -f > /dev/null
fi

# Run cis-server
echo "- Running ${CIS_SERVER_APP} application..."
docker run -it --name ${CIS_SERVER_APP} -d ${CIS_SERVER_IMAGE} > /dev/null
echo "  You can follow application logs by running 'docker logs -f ${CIS_SERVER_APP}'"


# Remove previously runned cis-collector application
docker ps -a | grep ${CIS_OS_COLLECTOR_APP} > /dev/null
if [ $? -eq 0 ]; then
    echo "- Remove previously runned ${CIS_OS_COLLECTOR_APP} application"
    docker rm ${CIS_OS_COLLECTOR_APP} -f > /dev/null
fi

# Run cis-openstack-collector
echo "- Running ${CIS_OS_COLLECTOR_APP} application and link it to ${CIS_SERVER} hostname"
docker run --name ${CIS_OS_COLLECTOR_APP} \
           --link ${CIS_SERVER_APP}:${CIS_SERVER} \
           --env-file oscollector-env \
            -d ${CIS_OS_COLLECTOR_IMAGE} > /dev/null
echo "  You can follow application logs by running 'docker logs -f ${CIS_OS_COLLECTOR_APP}'"


# Add containers to network
echo "- Add ${CIS_SERVER_APP} to ${CIS_CONTAINER_NETWORK} network"
docker network connect ${CIS_CONTAINER_NETWORK} ${CIS_SERVER_APP}
echo "- Add ${CIS_OS_COLLECTOR_APP} to ${CIS_CONTAINER_NETWORK} network"
docker network connect ${CIS_CONTAINER_NETWORK} ${CIS_OS_COLLECTOR_APP}



echo
echo "- Application deployment finished."

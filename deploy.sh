#!/bin/bash                                                                     
docker-compose down --rmi all --remove-orphans
docker-compose -f docker-compose-prod.yml up -d --build

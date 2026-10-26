# Intelligent-Load-Balancer
Build a load balaner other than normal HAProxy

We faced a latency issue due to each request will check 3 server for everytime. So we added a 250ms cache. So we will have the status of each server in there.
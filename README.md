# Online Store Project



Sales microservice ![Tests](https://github.com/gnm3000/coding-online-store/actions/workflows/sales.yml/badge.svg)
Customers microservice ![Tests](https://github.com/gnm3000/coding-online-store/actions/workflows/customers.yml/badge.svg)
Shipping microservice ![Tests](https://github.com/gnm3000/coding-online-store/actions/workflows/shipping.yml/badge.svg)

```console
foo@bar:~$ minikube start &&  minikube addons enable ingress

```


(k8s/mongodb)

```console
foo@bar:~$ cd k8s/mongodb && kubectl apply -f . 

```
wait 1 minute aprox unil ready 1/1

```console
foo@bar:~$ cd ../rabitmq/ 
foo@bar:~$ kubectl apply -f https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml
foo@bar:~$ kubectl apply -f rabbitmqcluster.yaml

```
Now we can deploy ours microservices. But before this, we need to build the images and push to dockerhub.
The files I execute were  docker-build-images.sh and docker-push-images.sh.
We will use the docker images I have already push to dockerhub


```console
foo@bar:~$ cd ../microservices/
foo@bar:~$ ./kubectl-apply-microservices.sh 
foo@bar:~$ kubectl get pods
foo@bar:~$ kubectl describe ingress online-store-ingress

```
With this command above, we deploy the microservices, then with get pods, I see when all of them is un running state.


192.168.49.2 is my minikube ip, get your minikube ip running in console:

```console
foo@bar:~$ minikube ip 

```

now we test if customers is running ok. It must return an array without elements "[]"

```console
foo@bar:~$ curl http://192.168.49.2/customers
[]
```

now we have all running in kubernates. Lets populate the DB and then run the bot

```console
foo@bar:~$ cd ../.. && cd bot
```

populate delete DB data and upload again using API sales and customers microservices.
I load 1000 customers with random wallet_usd and products to catalog store.

Attention => get your minikube IP and *edit* (bot/docker-compose.yml) with your IP (mine is 192.168.49.2)

```console
foo@bar:~$ docker compose up populate
```

this is the docker-container that will use 200 customers and make each order with 1-5 products for them

```console
foo@bar:~$ docker compose up run_bot
```
when it finish,


finally we get the summary and stats for customers. Go to the browser:
http://192.168.49.2/reporting/json (I can see json data)
http://192.168.49.2/reporting/csv-summary (It downloads a csv file)
http://192.168.49.2/reporting/csv-stats-by-customer (it downloads a csv file)


you can run locust
if you run. Then go to http://192.168.49.2:8089/ , select 200 users and only press Start swarming
if you want, you can run again populate before.

```console
foo@bar:~$ docker compose up run_locust
```



In /reporting/analysis-jupyter/analysis.ipynb you can see what I code to analyze the data from the different microservices before to code it as a downloadable file

### SwaggerAPI
- http://192.168.49.2/customers/api/docs
- http://192.168.49.2/sales/api/docs
- http://192.168.49.2/shipping/api/docs
- http://192.168.49.2/reporting/api/docs
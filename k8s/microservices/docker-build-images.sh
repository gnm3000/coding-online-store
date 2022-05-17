cd ../../shipping
echo "$(pwd)"
docker build -t gnm3000/shipping_microservice_worker:latest -f Dockerfile_worker .
docker build -t gnm3000/shipping_microservice:latest -f Dockerfile .
cd ../sales
echo "$(pwd)"
docker build -t gnm3000/sales_microservice_worker:latest -f Dockerfile_worker .
docker build -t gnm3000/sales_microservice:latest -f Dockerfile .

cd ../customers
echo "$(pwd)"
docker build -t gnm3000/customers_microservice_worker:latest -f Dockerfile_worker .
docker build -t gnm3000/customers_microservice:latest -f Dockerfile .


cd ../reporting
echo "$(pwd)"
docker build -t gnm3000/reporting_microservice:latest -f Dockerfile .
cd ..
echo "$(pwd)"
echo "ready"
# Example application to interact with the dutch trial site

## Building and publishing

```
docker build . --network=host -t ci.tno.nl:4567/envelope/eaas-deployment/example-experiment
docker push ci.tno.nl:4567/envelope/eaas-deployment/example-experiment
```

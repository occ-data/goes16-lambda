# Lambda GOES-16 Image Creator

This code downloads a multi-channel GOES-16 netcdf file when it recieves a SNS notification that the file has been created on S3 and creates an RGB png from the file. It then uploads the resulting png image back to a bucket.

## This code

This code has been adapted from https://github.com/perrygeo/lambda-rasterio. Thanks to them for figuring out the basic template of how to easily make, test, and package a python lambda function.

## Testing

You can test the main parts of the python code by using:
```
make test
```
Which utilizes `DockerfileTest` to load requirements.txt so they don't have to be reinstalled every time you want to test the app. This testing could be improved in the future to pass an actual example json to the lambda handler.

## Deploying

First set up a lambda function on AWS using python 2.7. Give it a name such as `goes16`. Set SNS on the left side of the Lambda with `arn:aws:sns:us-east-1:123901341784:NewGOES16Object` as the appropriate arn for the GOES-16 feed. Make sure to set the `Handler` in the lambda function to `handler.lambda_handler` so that this will work.

Build the necessary zip file using:
```
make
```

Upload the zip file to the lambda function:
```
aws lambda update-function-code --function-name goes16 --zip-file fileb://dist.zip --profile edc
```

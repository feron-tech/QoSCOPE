#!/bin/env bash

pushd application
pushd Artifacts/MCIOPs
tar -czvf app-example.tgz app-example
popd
zip -r app.zip * -x "Artifacts/MCIOPs/app-example/*"
mv app.zip ..
popd

echo "Application bundled."
read -p "Please provided the app id: " app_id

pushd experiment
sed "s/{{ APP_ID }}/$app_id/" <MyExperiment.yaml.template > MyExperiment.yaml
zip experiment.zip MyExperiment.mf MyExperiment.yaml
mv experiment.zip ..
popd

echo "Experiment bundled. Bye."

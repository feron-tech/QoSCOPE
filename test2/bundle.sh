#!/bin/env bash
set -euo pipefail

pushd application >/dev/null
pushd Artifacts/MCIOPs >/dev/null
tar -czvf nanomq.tgz nanomq
popd >/dev/null
zip -r app.zip * -x "Artifacts/MCIOPs/nanomq/*"
mv app.zip ..
popd >/dev/null

echo "Application bundled: app.zip"
read -p "Please provide the app id returned by the EaaS portal: " app_id

pushd experiment >/dev/null
sed "s/{{ APP_ID }}/$app_id/g" < NanoMQExperiment.yaml.template > NanoMQExperiment.yaml
zip experiment.zip NanoMQExperiment.mf NanoMQExperiment.yaml
mv experiment.zip ..
popd >/dev/null

echo "Experiment bundled: experiment.zip"

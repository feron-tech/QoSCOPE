# EaaS NanoMQ single-container test

This is a minimal EaaS package structure based on the provided working example.
It deploys one public Docker image:

```text
emqx/nanomq:latest
```

No application source code is included in `app.zip`; the Helm chart references the public container image directly.

## Structure

```text
application/
  NanoMQApplication.mf
  NanoMQApplication.yaml
  Artifacts/MCIOPs/nanomq/
    Chart.yaml
    values.yaml
    templates/deployment.yaml

experiment/
  NanoMQExperiment.mf
  NanoMQExperiment.yaml.template

bundle.sh
```

## Build packages

```bash
chmod +x bundle.sh
./bundle.sh
```

The script first creates:

```text
app.zip
```

Upload `app.zip` in the EaaS Applications tab. After the portal returns the Application ID, paste it into the script prompt. The script then creates:

```text
experiment.zip
```

Upload `experiment.zip` in the EaaS Experiments tab.

## Exposed port

The Helm service exposes MQTT TCP port `1883` through NodePort `32183`.
If the EaaS cluster rejects this fixed NodePort, edit:

```text
application/Artifacts/MCIOPs/nanomq/values.yaml
```

and either change `nodePort` or remove it.

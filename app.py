#!/usr/bin/env python3

import aws_cdk as cdk

from infrastructure.AirflowOnFargateStack import AirflowOnFargateStack

app = cdk.App()

AirflowOnFargateStack(
    app,
    "AirflowOnFargateStack",
)

app.synth()

#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.stacks.AirflowOnFargateStack import AirflowOnFargateStack

app = cdk.App()

AirflowOnFargateStack(
    app,
    "AirflowOnFargateStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()

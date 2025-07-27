#!/usr/bin/env python3
import os

import aws_cdk as cdk

from dueling_quibblers import DuelingQuibblersStack


app = cdk.App()
environment = app.node.try_get_context("environment")
DuelingQuibblersStack(
    app,
    "dueling-quibblers",
    env=cdk.Environment(region=environment["AWS_REGION"]),
    environment=environment,
)
app.synth()

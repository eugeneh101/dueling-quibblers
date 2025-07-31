import json

import cdk_ecr_deployment as ecr_deploy
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
)
from constructs import Construct


class EcsService(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, role: iam.Role
    ) -> None:
        super().__init__(scope, construct_id)  # required

        # create new AWS resources
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            vpc_name=environment["VPC"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                # ec2.SubnetConfiguration(
                #     name="Private-Subnet",
                #     subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                #     cidr_mask=24,
                # ),
            ],
            availability_zones=[
                f"{environment['AWS_REGION']}{az}"
                for az in environment["AVAILABILITY_ZONES"]
            ],
            # nat_gateways=len(environment["AVAILABILITY_ZONES"]),
        )
        self.security_group = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
        )
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(environment["ECS_PORT"]),
            description=(
                "Allow inbound TCP traffic from all IP addresses "
                "to Streamlit port (most likely 8501)"
            ),
        )

        self.ecs_cluster = ecs.Cluster(
            self,
            "EcsCluster",
            cluster_name=environment["ECS_CLUSTER"],
            vpc=self.vpc,
            container_insights_v2=ecs.ContainerInsights.ENABLED,
        )

        # connect AWS resources together
        self.ecr_repo = ecr.Repository(
            self,
            "EcrRepo",
            repository_name=environment["ECR_REPO"],
            empty_on_delete=True,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep only the latest image",
                    max_image_count=1,
                )
            ],
        )
        self.ecs_task_definition = self.ecs_task_definition(
            stack=self,
            task_definition_name=environment["ECS_TASK_DEFINITION"],
            task_directory="ecs/",  # hard coded
            ecr_repo=self.ecr_repo,
            ecs_port=environment["ECS_PORT"],
            role=role,
            env_vars={
                "AWS_REGION": environment["AWS_REGION"],
                "DEBATE_NUM_ROUNDS": json.dumps(environment["DEBATE_NUM_ROUNDS"]),
            },
            cloudwatch_group_already_created=environment[
                "CLOUDWATCH_GROUP_ALREADY_CREATED"
            ],
        )
        self.ecs_service = ecs.FargateService(
            self,
            "EcsService",
            service_name=environment["ECS_SERVICE"],
            cluster=self.ecs_cluster,
            task_definition=self.ecs_task_definition,
            desired_count=1,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True,  # seems to need to be True if using Public subnet
            enable_execute_command=environment["ECS_ENABLE_EXEC"],
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(capacity_provider="FARGATE_SPOT", weight=1)
            ],
            security_groups=[self.security_group],
        )

        if environment["ECS_SERVICE_AUTOMATIC_FORCE_RESTART"]:
            # Create Lambda function to force restart ECS service
            self.force_restart_ecs_service_lambda = _lambda.Function(
                self,
                "ForceRestartEcsServiceLambda",
                function_name=f"force-restart-{environment['ECS_SERVICE']}",
                handler="index.handler",
                timeout=Duration.seconds(10),
                runtime=_lambda.Runtime.PYTHON_3_12,
                environment={
                    "ECS_CLUSTER": self.ecs_cluster.cluster_name,
                    "ECS_SERVICE": self.ecs_service.service_name,
                },
                code=_lambda.Code.from_inline(
                    """
import os, boto3

def handler(event, context):
    print(f"event: {event}")
    ecs_cluster, ecs_service = os.environ["ECS_CLUSTER"], os.environ["ECS_SERVICE"]
    response = boto3.client("ecs").update_service(
        cluster=ecs_cluster,
        service=ecs_service,
        forceNewDeployment=True
    )
    print(
        f'Successfully triggered force restart for service "{ecs_service}" '
        f'in cluster "{ecs_cluster}": {response}'
    )
"""
                ),
                role=role,
            )

            self.ecr_push_rule = events.Rule(
                self,
                "EcrImagePushRule",
                rule_name=f"force-restart-{environment['ECS_SERVICE']}",
                event_pattern=events.EventPattern(
                    source=["aws.ecr"],
                    detail_type=["ECR Image Action"],
                    detail={
                        "repository-name": [environment["ECR_REPO"]],
                        "action-type": ["PUSH"],
                    },
                ),
                targets=[
                    events_targets.LambdaFunction(self.force_restart_ecs_service_lambda)
                ],
                description="Detects ECR image push events for ECS task",
            )

    @staticmethod
    def ecs_task_definition(
        stack: Stack,
        task_definition_name: str,
        task_directory: str,
        ecr_repo: ecr.Repository,
        ecs_port: int,
        role: iam.Role,
        env_vars: dict[str, str],
        cloudwatch_group_already_created: bool,
    ):
        """Mutates the stack"""
        task_asset = ecr_assets.DockerImageAsset(
            stack, f"EcrImage{task_definition_name}", directory=task_directory
        )  # uploads to `container-assets` ECR repo
        deploy_repo = ecr_deploy.ECRDeployment(  # upload to desired ECR repo
            stack,
            f"PushTaskImage{task_definition_name}",
            src=ecr_deploy.DockerImageName(task_asset.image_uri),
            dest=ecr_deploy.DockerImageName(ecr_repo.repository_uri),
            role=role,
        )
        if cloudwatch_group_already_created:
            log_group = logs.LogGroup.from_log_group_name(
                stack,
                f"TaskLogGroup{task_definition_name}",
                log_group_name=f"/ecs/{task_definition_name}",
            )
        else:
            log_group = logs.LogGroup(
                stack,
                f"TaskLogGroup{task_definition_name}",
                log_group_name=f"/ecs/{task_definition_name}",
                retention=logs.RetentionDays.ONE_YEAR,
                removal_policy=RemovalPolicy.RETAIN,
            )
        task_image = ecs.ContainerImage.from_ecr_repository(repository=ecr_repo)
        task_definition = ecs.TaskDefinition(
            stack,
            f"TaskDefinition{task_definition_name}",
            family=task_definition_name,
            compatibility=ecs.Compatibility.FARGATE,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64,
            ),
            cpu="256",  # 0.25 CPU
            memory_mib="512",  # 0.5 GB RAM
            # ephemeral_storage_gib=None,
            # volumes=None,
            execution_role=role,
            task_role=role,
        )
        container = task_definition.add_container(
            task_definition_name,
            image=task_image,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ecs",
                log_group=log_group,
                mode=ecs.AwsLogDriverMode.NON_BLOCKING,
            ),
            environment=env_vars,
        )
        container.add_port_mappings(
            ecs.PortMapping(container_port=ecs_port, host_port=ecs_port)
        )

        # make sure repo created before task definition
        task_definition.node.add_dependency(deploy_repo)

        return task_definition


class DuelingQuibblersStack(Stack):

    def __init__(
        self, scope: Construct, construct_id: str, environment: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create new AWS resources
        self.ecs_role = iam.Role(
            self,
            "EcsTaskExecutionRole",
            role_name=environment["IAM_ROLE"].format(
                AWS_REGION=environment["AWS_REGION"]
            ),
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )  ### principle of least privileges later,
            ],
        )
        self.ecs_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:*:*:inference-profile/*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        self.ecs_role.add_to_policy(
            iam.PolicyStatement(  # for ecr_deploy.ECRDeployment
                actions=[
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage",
                ],
                resources=[
                    f"arn:aws:ecr:{environment['AWS_REGION']}:*:"
                    f"repository/{environment['ECR_REPO']}"
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        if environment["ECS_SERVICE_AUTOMATIC_FORCE_RESTART"]:
            self.ecs_role.assume_role_policy.add_statements(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[
                        iam.ServicePrincipal("lambda.amazonaws.com"),
                    ],
                    actions=["sts:AssumeRole"],
                )
            )
            self.ecs_role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            )
            self.ecs_role.add_to_policy(
                iam.PolicyStatement(
                    actions=["ecs:UpdateService"],
                    resources=[
                        f"arn:aws:ecs:{environment['AWS_REGION']}:*:service/"
                        f"{environment['ECS_CLUSTER']}/{environment['ECS_SERVICE']}"
                    ],
                )
            )

        self.ecs_service = EcsService(
            scope=self,
            construct_id=environment["ECS_SERVICE"],
            environment=environment,
            role=self.ecs_role.without_policy_updates(),  # prevent role mutation
        )

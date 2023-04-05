from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
)
from aws_cdk.aws_iam import ManagedPolicy
from constructs import Construct

from infrastructure.config import worker_autoscaling_config


class ServiceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        default_security_group: ec2.SecurityGroup,
        cluster: ecs.Cluster,
        task_definition: ecs.FargateTaskDefinition,
        is_worker_service: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(scope, id)

        # Attach required policies to the Task Role
        policies = [
            ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess"),
            ManagedPolicy.from_aws_managed_policy_name("AmazonECS_FullAccess"),
            ManagedPolicy.from_aws_managed_policy_name(
                "AmazonElasticFileSystemClientReadWriteAccess"
            ),
            ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsReadOnlyAccess"),
        ]
        for policy in policies:
            task_definition.task_role.add_managed_policy(policy)

        # Create a Fargate Service for Airflow
        self._fargate_service = ecs.FargateService(
            self,
            id,
            cluster=cluster,
            task_definition=task_definition,
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
            security_groups=[default_security_group],
        )
        allowed_ports = ec2.Port(
            protocol=ec2.Protocol.TCP,
            string_representation="All",
            from_port=0,
            to_port=65535,
        )
        self._fargate_service.connections.allow_from_any_ipv4(allowed_ports)
        if is_worker_service:
            self.configure_autoscaling()
        else:
            self._load_balancer_dns_name = CfnOutput(
                self, "LoadBalancerDNSName", value=self.attach_load_balancer(vpc)
            )

    def attach_load_balancer(self, vpc: ec2.Vpc) -> str:
        # Create a load balancer for the service
        load_balancer = elbv2.NetworkLoadBalancer(
            self,
            f"{id}LoadBalancer",
            vpc=vpc,
            internet_facing=True,
            cross_zone_enabled=True,
        )

        # Create a listener for the service
        listener = load_balancer.add_listener(
            f"{id}Listener",
            port=80,
        )

        # Add a target group for the service
        target_group = listener.add_targets(
            f"{id}TargetGroup",
            port=80,
            targets=[self._fargate_service],
            health_check=elbv2.HealthCheck(
                healthy_threshold_count=2,
                unhealthy_threshold_count=2,
            ),
        )
        target_group.set_attribute("deregistration_delay.timeout_seconds", "60")
        return load_balancer.load_balancer_dns_name

    def configure_autoscaling(self):
        # Create an autoscaling policy for the service
        scaling = self._fargate_service.auto_scale_task_count(
            max_capacity=worker_autoscaling_config.max_capacity,
            min_capacity=worker_autoscaling_config.min_capacity,
        )
        if worker_autoscaling_config.target_cpu_utilization is not None:
            scaling.scale_on_cpu_utilization(
                "CpuScaling",
                target_utilization_percent=worker_autoscaling_config.target_cpu_utilization,
                scale_in_cooldown=Duration.seconds(60),
                scale_out_cooldown=Duration.seconds(60),
            )
        if worker_autoscaling_config.target_memory_utilization is not None:
            scaling.scale_on_memory_utilization(
                "MemoryScaling",
                target_utilization_percent=worker_autoscaling_config.target_memory_utilization,
                scale_in_cooldown=Duration.seconds(60),
                scale_out_cooldown=Duration.seconds(60),
            )

    @property
    def fargate_service(self) -> ecs.FargateService:
        return self._fargate_service

    @property
    def load_balancer_dns_name(self) -> CfnOutput:
        return self._load_balancer_dns_name

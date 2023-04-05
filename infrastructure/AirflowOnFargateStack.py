from aws_cdk import aws_ec2 as ec2, aws_ecs as ecs, Stack, Tags
from constructs import Construct

from infrastructure.constructs.AirflowConstruct import AirflowConstruct
from infrastructure.constructs.DagTasksConstruct import DagTasksConstruct
from infrastructure.constructs.DatabaseConstruct import DatabaseConstruct


class AirflowOnFargateStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a VPC with 2 AZs
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=2,
        )
        Tags.of(self).add("Stack", "AirflowOnFargate")

        # Create an ECS cluster
        cluster = ecs.Cluster(
            self,
            "ECSCluster",
            vpc=vpc,
        )

        # Create a default security group
        default_security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
        )

        # Create a database stack with a PostgreSQL database instance for Airflow
        db = DatabaseConstruct(
            self,
            "RDS-PostgreSQL",
            vpc=vpc,
            default_security_group=default_security_group,
        )

        # Create an Airflow stack with a webserver service, a worker service, and a scheduler service
        AirflowConstruct(
            self,
            "AirflowService",
            vpc=vpc,
            default_security_group=default_security_group,
            cluster=cluster,
            db_connection_string=db.db_connection_string,
            private_subnet_ids=vpc.private_subnets,
        )

        # Create Task Definitions for on-demand Fargate Tasks invoked from DAGs
        DagTasksConstruct(
            self,
            "DagTasks",
            vpc=vpc,
            default_security_group=default_security_group,
        )

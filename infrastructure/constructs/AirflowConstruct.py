from aws_cdk import aws_ec2 as ec2, aws_ecs as ecs, Stack, CfnOutput
from constructs import Construct
from aws_cdk.aws_ecr_assets import DockerImageAsset, Platform
from infrastructure.config import airflow_task_config
from infrastructure.constructs.ServiceConstruct import ServiceConstruct
from uuid import uuid4


class AirflowConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        cluster: ecs.Cluster,
        db_connection_string: str,
        default_security_group: ec2.SecurityGroup,
        private_subnet_ids: list[ec2.ISubnet],
        **kwargs,
    ) -> None:
        super().__init__(scope, id)
        admin_password = str(uuid4())

        # Set environment variables
        environment = {
            "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": db_connection_string,
            "AIRFLOW__CORE__EXECUTOR": "CeleryExecutor",
            "AIRFLOW__CELERY__BROKER_URL": "sqs://",
            "AIRFLOW__CELERY__RESULT_BACKEND": f"db+{db_connection_string}",
            "AIRFLOW__WEBSERVER__RBAC": "True",
            "ADMIN_PASSWORD": admin_password,
            "CLUSTER": cluster.cluster_name,
            "SUBNETS": ",".join([subnet.subnet_id for subnet in private_subnet_ids]),
            "SECURITY_GROUP": default_security_group.security_group_id,
        }

        logging = ecs.AwsLogDriver(
            stream_prefix="AirflowLogs",
            log_retention=airflow_task_config.log_retention,
        )

        # Build Airflow docker image
        airflow_image_asset = DockerImageAsset(
            self,
            "AirflowImage",
            directory="./airflow",
            platform=Platform.LINUX_AMD64
        )

        # Create task definitions
        airflow_task = ecs.FargateTaskDefinition(
            self,
            "AirflowTask",
            cpu=airflow_task_config.cpu,
            memory_limit_mib=airflow_task_config.memory,
        )
        if airflow_task_config.create_worker_pool:
            worker_task = ecs.FargateTaskDefinition(
                self,
                "WorkerTask",
                cpu=airflow_task_config.cpu,
                memory_limit_mib=airflow_task_config.memory,
            )
        else:
            worker_task = airflow_task

        # Map containers to task definitions
        task_containers = {
            airflow_task_config.webserver_config: airflow_task,
            airflow_task_config.scheduler_config: airflow_task,
            airflow_task_config.worker_config: worker_task,
        }

        # Create containers
        for container_config, task_definition in task_containers.items():
            container = task_definition.add_container(
                container_config.name,
                image=ecs.ContainerImage.from_docker_image_asset(airflow_image_asset),
                environment=environment,
                logging=logging,
                entry_point=[container_config.entry_point],
            )
            container.add_port_mappings(
                ecs.PortMapping(container_port=container_config.container_port)
            )

        # Create service
        ServiceConstruct(
            self,
            "AirflowService",
            cluster=cluster,
            task_definition=airflow_task,
            vpc=vpc,
            default_security_group=default_security_group,
        )
        if airflow_task_config.create_worker_pool:
            ServiceConstruct(
                self,
                "WorkerService",
                cluster=cluster,
                task_definition=worker_task,
                vpc=vpc,
                default_security_group=default_security_group,
                is_worker_service=True,
            )

        # Output admin password
        CfnOutput(
            self,
            "AdminPassword",
            value=admin_password,
        )

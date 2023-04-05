from aws_cdk import (
    aws_efs as efs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
)
from constructs import Construct
from infrastructure.constructs.TaskConstruct import TaskConstruct


class DagTasksConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        default_security_group: ec2.SecurityGroup,
    ) -> None:
        super().__init__(scope, id)

        logging = ecs.AwsLogDriver(
            stream_prefix="AirflowOnFargateDagTaskLogging",
            log_group=logs.LogGroup(
                self,
                "AirflowOnFargateDagTaskLogGroup",
                log_group_name="AirflowOnFargateDagTaskLogGroup",
                retention=logs.RetentionDays.ONE_MONTH,
            ),
        )

        shared_efs_file_system = efs.FileSystem(
            self,
            "AirflowOnFargateDagTaskFileSystem",
            vpc=vpc,
            security_group=default_security_group,
        )
        shared_efs_file_system.connections.allow_internally(ec2.Port.tcp(2049))

        # Task container with multiple python executables
        TaskConstruct(
            self,
            "AirflowOnFargateCombinedTask",
            task_family_name="AirflowOnFargateCombinedTask",
            container_name="MultiTaskContainer",
            container_asset_dir="./infrastructure/tasks/multi_task",
            cpu=512,
            memory=1024,
            logging=logging,
            efs_volume_name="AirflowSharedVolume",
            efs_file_system_id=shared_efs_file_system.file_system_id,
            efs_container_path="/airflow-shared-volume",
        )

        # Task container with single python executable
        TaskConstruct(
            self,
            "AirflowOnFargateSingleTask",
            task_family_name="AirflowOnFargateSingleTask",
            container_name="SingleTaskContainer",
            container_asset_dir="./infrastructure/tasks/single_task",
            cpu=256,
            memory=512,
            logging=logging,
            efs_volume_name="AirflowSharedVolume",
            efs_file_system_id=shared_efs_file_system.file_system_id,
            efs_container_path="/airflow-shared-volume",
        )

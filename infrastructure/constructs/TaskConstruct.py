from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
)
from aws_cdk.aws_ecr_assets import DockerImageAsset
from aws_cdk.aws_iam import ManagedPolicy
from constructs import Construct


class TaskConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        task_family_name: str,
        container_name: str,
        container_asset_dir: str,
        cpu: int,
        memory: int,
        logging: ecs.LogDriver,
        efs_volume_name: str | None,
        efs_container_path: str | None,
        efs_file_system_id: str | None,
    ) -> None:
        super().__init__(scope, f"{id}-TaskConstruct")

        worker_task = ecs.FargateTaskDefinition(
            self,
            f"{id}-TaskDefinition",
            family=task_family_name,
            cpu=cpu,
            memory_limit_mib=memory,
        )
        if efs_file_system_id is not None:
            worker_task.add_volume(
                name=efs_volume_name,
                efs_volume_configuration=ecs.EfsVolumeConfiguration(
                    file_system_id=efs_file_system_id,
                ),
            )

            worker_task.task_role.add_managed_policy(
                ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonElasticFileSystemClientReadWriteAccess"
                )
            )

        worker_image_asset = DockerImageAsset(
            self,
            f"{container_name}-BuildImage",
            directory=container_asset_dir,
        )

        container = worker_task.add_container(
            container_name,
            image=ecs.ContainerImage.from_docker_image_asset(worker_image_asset),
            logging=logging,
        )
        if efs_file_system_id is not None:
            container.add_mount_points(
                ecs.MountPoint(
                    container_path=efs_container_path,
                    source_volume=efs_volume_name,
                    read_only=False,
                )
            )

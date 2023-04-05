from aws_cdk.aws_logs import RetentionDays
from aws_cdk.aws_ec2 import InstanceType, InstanceClass, InstanceSize


class ContainerConfig:
    def __init__(
        self,
        name: str,
        container_port: int,
        entry_point: str,
        cpu: int = 256,
        memory: int = 512,
    ):
        self.entry_point = entry_point
        self.container_port = container_port
        self.name = name
        self.cpu = cpu
        self.memory = memory


class AirflowTaskConfig:
    def __init__(
        self,
        cpu: int,
        memory: int,
        webserver_config: ContainerConfig,
        scheduler_config: ContainerConfig,
        worker_config: ContainerConfig,
        log_retention: RetentionDays,
        create_worker_pool: bool = False,
    ):
        self.cpu = cpu
        self.memory = memory
        self.webserver_config = webserver_config
        self.scheduler_config = scheduler_config
        self.worker_config = worker_config
        self.log_retention = log_retention
        self.create_worker_pool = create_worker_pool


class AutoScalingConfig:
    def __init__(
        self,
        min_capacity: int,
        max_capacity: int,
        target_memory_utilization: int = 80,
        target_cpu_utilization: int = 80,
    ):
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.target_memory_utilization = target_memory_utilization
        self.target_cpu_utilization = target_cpu_utilization


class DBConfig:
    def __init__(
        self,
        db_name: str,
        db_master_user: str,
        db_port: int,
        db_instance_type: InstanceType,
        db_storage_size: int,
        db_backup_retention: int,
    ):
        self.db_name = db_name
        self.db_master_user = db_master_user
        self.db_port = db_port
        self.db_instance_type = db_instance_type
        self.db_storage_size = db_storage_size
        self.db_backup_retention = db_backup_retention


worker_autoscaling_config = AutoScalingConfig(
    min_capacity=1,
    max_capacity=5,
    target_cpu_utilization=70,
)

default_webserver_config = ContainerConfig(
    name="webserver", container_port=8080, entry_point="/webserver_entry.sh"
)

default_scheduler_config = ContainerConfig(
    name="scheduler", container_port=8081, entry_point="/scheduler_entry.sh"
)

default_worker_config = ContainerConfig(
    name="worker", container_port=8082, entry_point="/worker_entry.sh"
)

airflow_task_config = AirflowTaskConfig(
    cpu=2048,
    memory=4096,
    webserver_config=default_webserver_config,
    scheduler_config=default_scheduler_config,
    worker_config=default_worker_config,
    log_retention=RetentionDays.ONE_MONTH,
    # To have a dedicated worker pool, set this to True
    # create_worker_pool=True
)

default_db_config = DBConfig(
    db_name="airflow",
    db_master_user="airflow",
    db_port=5432,
    db_instance_type=InstanceType.of(
        InstanceClass.T3,
        InstanceSize.SMALL,
    ),
    db_storage_size=25,
    db_backup_retention=30,
)

import json

from aws_cdk import (
    Duration,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    Stack,
)
from constructs import Construct
from infrastructure.config import default_db_config, DBConfig


class DatabaseStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: ec2.Vpc,
        default_security_group: ec2.SecurityGroup,
        db_config: default_db_config = default_db_config,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        backend_secret = secretsmanager.Secret(
            self,
            "BackendSecret",
            secret_name=f"{id}Secret",
            description="Secrets for the airflow database",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "username": db_config.db_master_user,
                    }
                ),
                generate_string_key="password",
                exclude_punctuation=True,
                include_space=False,
                exclude_numbers=False,
                exclude_uppercase=False,
                exclude_lowercase=False,
                password_length=16,
                require_each_included_type=False,
            ),
        )
        self._db_password = backend_secret.secret_value_from_json("password")
        self._db = rds.DatabaseInstance(
            self,
            "AirflowDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_13_2
            ),
            instance_type=db_config.db_instance_type,
            vpc=vpc,
            instance_identifier=default_db_config.db_name,
            security_groups=[default_security_group],
            storage_encrypted=True,
            deletion_protection=False,
            backup_retention=Duration.days(default_db_config.db_backup_retention),
            database_name=default_db_config.db_name,
            credentials=rds.Credentials.from_password(
                username=default_db_config.db_master_user,
                password=self._db_password,
            ),
            allocated_storage=default_db_config.db_storage_size,
            auto_minor_version_upgrade=False,
            port=default_db_config.db_port,
        )

    @property
    def db(self):
        return self._db

    @property
    def db_password(self):
        return self._db_password

    @property
    def db_connection_string(self):
        return get_db_connection_string(
            default_db_config,
            self.db.db_instance_endpoint_address,
            self.db_password.to_string(),
        )


def get_db_connection_string(db_config: DBConfig, endpoint: str, password: str) -> str:
    return (
        f"postgresql+psycopg2://{db_config.db_master_user}:{password}@{endpoint}:{db_config.db_port}"
        f"/{db_config.db_name}"
    )

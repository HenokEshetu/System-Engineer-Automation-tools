import boto3
import datetime

ec2 = boto3.client("ec2")


def create_snapshots():
    volumes = ec2.describe_volumes(Filters=[{"Name": "tag:Backup", "Values": ["True"]}])
    for vol in volumes["Volumes"]:
        vol_id = vol["VolumeId"]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"Creating snapshot for Volume {vol_id}")
        ec2.create_snapshot(
            VolumeId=vol_id,
            Description=f"Automated backup {date}",
            TagSpecifications=[
                {
                    "ResourceType": "snapshot",
                    "Tags": [{"Key": "Backup", "Value": "True"}],
                }
            ],
        )


create_snapshots()

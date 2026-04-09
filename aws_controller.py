import boto3
import pandas as pd
from datetime import datetime
import pytz

def get_aws_inventory():
    regions = ['us-east-1'] 
    inventory, orphaned_volumes, unassociated_ips = [], [], []
    account_identity = "Produção (AWS Master)"
    fuso_br = pytz.timezone('America/Sao_Paulo')

    print(f"🚀 Iniciando coleta consolidada...")

    for region in regions:
        try:
            ec2 = boto3.client('ec2', region_name=region)
            
            # 1. INSTÂNCIAS
            res = ec2.describe_instances()
            for reservation in res['Reservations']:
                for inst in reservation['Instances']:
                    tags = {tag['Key']: tag['Value'] for tag in inst.get('Tags', [])}
                    
                    # Soma de Discos
                    v_ids = [b['Ebs']['VolumeId'] for b in inst.get('BlockDeviceMappings', []) if 'Ebs' in b]
                    total_gb = sum([v['Size'] for v in ec2.describe_volumes(VolumeIds=v_ids)['Volumes']]) if v_ids else 0

                    inventory.append({
                        "Conta": account_identity, "Name": tags.get('Name', 'Sem Nome'),
                        "Instance ID": inst['InstanceId'], "Tipo": inst['InstanceType'],
                        "IP Privado": inst.get('PrivateIpAddress', 'N/A'),
                        "SO": "Windows" if inst.get('Platform') == 'windows' else "Linux",
                        "Disco (GB)": total_gb, "Status": "Ligado" if inst['State']['Name'] == 'running' else "Desligado",
                        "Backup": "Sim" if tags.get('Backup') in ['True', 'Sim', 'Yes'] else "Não",
                        "Lançamento": inst['LaunchTime'].astimezone(fuso_br).strftime('%d/%m/%Y %H:%M')
                    })

            # 2. VOLUMES ÓRFÃOS
            vols = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
            for v in vols.get('Volumes', []):
                orphaned_volumes.append({
                    "Volume ID": v['VolumeId'], "Tamanho (GB)": v['Size'],
                    "Criação": v['CreateTime'].astimezone(fuso_br).strftime('%d/%m/%Y %H:%M')
                })

            # 3. IPs SOLTOS
            eips = ec2.describe_addresses()
            for ip in eips.get('Addresses', []):
                if 'InstanceId' not in ip:
                    unassociated_ips.append({"IP Público": ip['PublicIp'], "Região": region})

        except Exception as e:
            print(f"❌ Erro em {region}: {e}")

    # Salva CSVs (Garante que nunca fiquem vazios para não quebrar o app)
    pd.DataFrame(inventory).to_csv('inventory_data.csv', index=False)
    pd.DataFrame(orphaned_volumes if orphaned_volumes else None, columns=["Volume ID", "Tamanho (GB)", "Criação"]).to_csv('orphaned_volumes.csv', index=False)
    pd.DataFrame(unassociated_ips if unassociated_ips else None, columns=["IP Público", "Região"]).to_csv('unassociated_ips.csv', index=False)
    print("✅ Dados atualizados!")

if __name__ == "__main__":
    get_aws_inventory()
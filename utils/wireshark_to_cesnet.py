import pandas as pd
import numpy as np

def convert_wireshark_to_cesnet(csv_path, window_minutes=10):
    """
    Convertit un CSV Wireshark enrichi en features CESNET
    en agrégeant par fenêtres de temps
    """
    # Charger le CSV
    df = pd.read_csv(csv_path)
    print(f"Paquets capturés : {len(df)}")
    
    # Nettoyer
    df = df.dropna(subset=['ip.src', 'ip.dst'])
    df['frame.time_epoch'] = pd.to_numeric(df['frame.time_epoch'], errors='coerce')
    df['frame.len'] = pd.to_numeric(df['frame.len'], errors='coerce').fillna(0)
    df['ip.ttl'] = pd.to_numeric(df['ip.ttl'], errors='coerce').fillna(0)
    df['ip.proto'] = pd.to_numeric(df['ip.proto'], errors='coerce').fillna(0)
    df['tcp.dstport'] = pd.to_numeric(df['tcp.dstport'], errors='coerce').fillna(0)
    df['udp.dstport'] = pd.to_numeric(df['udp.dstport'], errors='coerce').fillna(0)
    df['frame.time_delta'] = pd.to_numeric(df['frame.time_delta'], errors='coerce').fillna(0)
    
    # Créer une fenêtre temporelle
    df['window'] = (df['frame.time_epoch'] // (window_minutes * 60)).astype(int)
    
    # Agréger par IP source et fenêtre temporelle
    results = []
    for (ip_src, window), group in df.groupby(['ip.src', 'window']):
        
        # Calcul des features CESNET
        n_packets = len(group)
        n_bytes = group['frame.len'].sum()
        n_dest_ip = group['ip.dst'].nunique()
        
        # Ports destination (TCP + UDP)
        tcp_ports = group[group['tcp.dstport'] > 0]['tcp.dstport'].nunique()
        udp_ports = group[group['udp.dstport'] > 0]['udp.dstport'].nunique()
        n_dest_ports = tcp_ports + udp_ports
        
        # Flows (paires src-dst distinctes)
        n_flows = group.groupby(['ip.src', 'ip.dst']).ngroups
        
        # n_dest_asn (approximé par n_dest_ip car pas d'ASN disponible)
        n_dest_asn = n_dest_ip
        
        # Ratio TCP/UDP
        tcp_packets = len(group[group['ip.proto'] == 6])
        udp_packets = len(group[group['ip.proto'] == 17])
        total_tu = tcp_packets + udp_packets
        tcp_udp_ratio_packets = tcp_packets / total_tu if total_tu > 0 else 0.5
        tcp_bytes = group[group['ip.proto'] == 6]['frame.len'].sum()
        udp_bytes = group[group['ip.proto'] == 17]['frame.len'].sum()
        total_bytes_tu = tcp_bytes + udp_bytes
        tcp_udp_ratio_bytes = tcp_bytes / total_bytes_tu if total_bytes_tu > 0 else 0.5
        
        # Ratio directionnel (sortant vs total)
        outgoing = len(group[group['ip.src'] == ip_src])
        dir_ratio_packets = outgoing / n_packets if n_packets > 0 else 0.5
        outgoing_bytes = group[group['ip.src'] == ip_src]['frame.len'].sum()
        dir_ratio_bytes = outgoing_bytes / n_bytes if n_bytes > 0 else 0.5
        
        # Durée moyenne et TTL
        avg_duration = group['frame.time_delta'].mean()
        avg_ttl = group['ip.ttl'].mean()
        
        results.append({
            'n_flows': n_flows,
            'n_packets': n_packets,
            'n_bytes': n_bytes,
            'n_dest_asn': n_dest_asn,
            'n_dest_ports': n_dest_ports,
            'n_dest_ip': n_dest_ip,
            'tcp_udp_ratio_packets': tcp_udp_ratio_packets,
            'tcp_udp_ratio_bytes': tcp_udp_ratio_bytes,
            'dir_ratio_packets': dir_ratio_packets,
            'dir_ratio_bytes': dir_ratio_bytes,
            'avg_duration': avg_duration,
            'avg_ttl': avg_ttl
        })
    
    df_cesnet = pd.DataFrame(results)
    print(f"Lignes CESNET générées : {len(df_cesnet)}")
    return df_cesnet


if __name__ == "__main__":
    # Convertir la capture Wireshark
    df_cesnet = convert_wireshark_to_cesnet('data/capture_long.csv', window_minutes=1)
    print("\nAperçu des données converties :")
    print(df_cesnet.head())
    print(f"\nShape : {df_cesnet.shape}")
    
    # Sauvegarder
    df_cesnet.to_csv('data/capture_long_cesnet.csv', index=False)
    print("\nFichier sauvegardé : data/capture_long_cesnet.csv ")
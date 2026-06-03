# Configuration des VMs

## VM1 - Machine Normale
- IP : 192.168.56.10
- Hostname : vm1-normal
- OS : Ubuntu 22.04 LTS
- Rôle : Générer du trafic + capturer avec tshark

## VM2 - Serveur Cible
- IP : 192.168.56.20
- Hostname : vm2-serveur
- OS : Ubuntu 22.04 LTS
- Rôle : Recevoir le trafic

## Commandes utiles
- Lancer les VMs : vagrant up
- Se connecter VM1 : vagrant ssh vm1
- Capturer le trafic : tshark -i enp0s8 -a duration:30 -w /vagrant/capture.pcap
- Arrêter les VMs : vagrant halt
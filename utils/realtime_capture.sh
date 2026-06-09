#!/bin/bash
echo " Capture temps réel démarrée..."

while true; do
    echo " Capture 10 secondes..."
    
    tshark -i enp0s8 -a duration:10 \
    -T fields \
    -e ip.src -e ip.dst -e ip.proto \
    -e frame.len -e tcp.dstport -e udp.dstport \
    -e ip.ttl -e frame.time_delta -e tcp.flags \
    -e ip.len -e frame.time_epoch \
    -e tcp.srcport -e udp.srcport \
    -E header=y -E separator=, \
    > /vagrant/data/realtime_capture.csv 2>/dev/null
    
    echo " Capture terminée → envoi vers Redis"
    
    python3 /vagrant/utils/realtime_producer.py
    
    echo " Capture prochaine dans 2 secondes..."
    sleep 2
done
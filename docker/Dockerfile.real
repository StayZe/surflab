FROM --platform=linux/amd64 cm2network/steamcmd:root

# Dépendances système pour Source 2
RUN apt-get update && apt-get install -y \
    libicu-dev libsqlite3-0 libnet1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

USER steam
WORKDIR /home/steam/cs2-dedicated

# Script de lancement : Téléchargement + Exécution
# On ajoute +sv_setsteamaccount pour le GSLT (indispensable en prod)
CMD /home/steam/steamcmd/steamcmd.sh +force_install_dir /home/steam/cs2-dedicated +login anonymous +app_update 730 validate +quit && \
    ./game/bin/linuxsteamrt64/cs2 -dedicated \
    -port $CS2_PORT \
    +map $CS2_MAP \
    -authkey $STEAM_API_KEY \
    +host_workshop_map $CS2_WORKSHOP_ID \
    +sv_setsteamaccount $GSLT_TOKEN
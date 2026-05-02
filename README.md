# leafet_lab

local server : 
python -m http.server 8000
flask --app main.py run --host 0.0.0.0

persistence : aurora dsql, orm : alchemy, db migration : alembic
authent : google



Specs : 
- gestion des collections 
- nom du parcours
- type de parcours
- propriétaire
- visibilité (pub/priv)
- login (google ou okta)
- gpx => add from url ou upload
- put tag on trail
- gestion des langues sur la carte

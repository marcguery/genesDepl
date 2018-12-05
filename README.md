# Base de données ENSEMBL

## Mise en place

1. Modifiez le fichier *classes/dbInfos.py* pour y intégrer vos propres informations concernant la base de données ENSEMBL.
   - **location** : le dossier dans lequel est/sont stockées les bases de données.
   - **dbtype** : le type de base de données. Les valeurs acceptées sont *sql* et *sqlite.*
   - **log** : le chemin du fichier log.
   - **detail** : le fichier JSON contenant vos informations personnelles concernant les bases de données.
2. Créez ensuite le fichier JSON ''**detail**'' que vous avez mentionné dans le fichier *classes/dbInfos.py* **à l'aide du template**.
   - **login** : votre login sur mySQL.
   - **password** : votre mot de passe sur mySQL.
   - **host** : le nom de l'hôte pour mySQL.
   - **database** : le nom de la base de données (mySQL) ou le nom du fichier (sqlite).
3. Lancez ensuite le script *run.sh* ou bien *app.py*.

```bash
bash run.sh
```

Ou

```bash
python3 app.py
```



## Version

- 5/12/2018

## Contact

Marc-Antoine Guery

marc-antoine.guery@etu.univ-lyon.fr

M2 bioinformatique
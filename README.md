# CSV to Database importer

This is an additional feature for the ohtuilmo application.

This repository contains scripts for importing data from CSV files into a database. The feature is used by deploying an app to OpenShift, copying csv files to pod, and then running scripts inside pod.

## How to use import feature via OpenShift CLI (oc)

### Pre-requisites

Make sure that:

- You are connected to Helsinki University's network either directly or via VPN
- You have OpenShift command-line interface CLI (the oc command) installed on your computer. For more information, check [this](https://wiki.helsinki.fi/xwiki/bin/view/SO/Sovelluskehitt%C3%A4j%C3%A4n%20ohjeet/Alustat/Tiken%20konttialusta/)

### 1. Prepare correct folder structure

Make sure you have following folder structure:

```
<your_current_folder>/
├── sprint_data/
└── timelogs_data/
```

Place sprint CSVs inside sprint_data folder and timelog CSVs inside timelogs_data folder. In next steps, it is assumed that you give commands from folder witch includes folders above.

**Required data format for files in sprint_data:**

```
group name;sprint (number 0-);start date (yyyy-mm-dd);end date (yyyy-mm-dd)
```

eg.

```
Ohtuprojektien ilmoittautumisjärjestelmä;1;2024-1-17;2024-1-24
```

Note that the group name has to exactly the one used in Ohtuilmo app. Note also the date format!

**Required data format for files in timelogs_data:**

```
student number;sprint (number 0-);hours;date (yyyy-mm-dd);textual description of the work
```

eg.

```
012345678;1;3,5;2024-1-20;Vein sovelluksen onnistuneesti OpenShiftiin
```

Note the decimal format!

Ensure that neither of the files contains empty rows.

### 2. Login to oc

For login, you have two options. You can login via your browser with command:

```
oc login --web
```

Alternatively, you can login via command line with command:

```
oc login -u <username> https://api.ocp-test-0.k8s.it.helsinki.fi:6443
```

Use your university username and password. The username format is 'elallone' for person Ella Allonen, for example.

### 3. Create a new app to OpenShift

Deploy a new app to OpenShift based on importscript image in quay.io with command:

```
oc new-app quay.io/ohtuilmo/importscript
```

This will deploy an app called importscript to OpenShift and start one pod.

### 4. Add DATABASE_URL environment variable to pod

You need to set DATABASE_URL environment variable for app so it can connect to database. If DATABASE_URL is already configured on OpenShift as a secret, you can re-use it with command:

```
oc set env --from=secret/<your_secret_name> deployment/importscript
```

For example, on our staging the DATABASE_URL is configured on secret named 'ohtuilmo-config', and it can be imported with command `oc set env --from=secret/ohtuilmo-config deployment/importscript`

### 5. Copy sprint_data folder to pod

Copy sprint_data folder to pod with command:

```
oc rsync ./sprint_data $(oc get pods -l deployment=importscript -o name):/tmp
```

### 6. Execute importSprint script

The importSprints script will write sprint information from csv files to database. Execute the script with command:

```
oc exec $(oc get pods -l deployment=importscript -o name) -- python scripts/importSprints.py
```

The script will inform you if there are fault lines in CSV files. In case you get errors, fix the fault CSVs on your own machine and then try again by following instructions from step 5.

Please note that valid sprints must be added to database before trying to add timelogs.

### 7. Copy the timelogs_data folder to pod

Copy timelogs_data folder to pod with command:

```
oc rsync ./timelogs_data $(oc get pods -l deployment=importscript -o name):/tmp
```

### 8. Execute importTimeLogs script

The importTimeLogs script will write timelogs information from csv files to database. Execute the script with command:

```
oc exec $(oc get pods -l deployment=importscript -o name) -- python scripts/importTimeLogs.py
```

The script will inform you if there are fault lines in CSV files. In case you get errors, fix the fault CSVs on your own machine and then try again by following instructions from step 7.

### 8. Delete the app

When you are ready, you can delete the app from OpenShift with command:

```
oc delete all -l app=importscript
```

This will remove the deployment and imagestream related to importscript app.

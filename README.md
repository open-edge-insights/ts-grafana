## README FOR GRAFANA ##

# GRAFANA #

1. Grafana is an open source metric analytics & visualization suite. It is most commonly used for visualizing time series data for infrastructure and        application analytics but many use it in other domains including industrial sensors, home automation, weather, and process control.
2. Grafana supports many different storage backends for our time series data (Data Source). Here in EIS we are using InfluxDB as datasource.
3. Grafana connects to the InfluxDB datasource which has been preconfigured as a part of grafana setup. The data source i.e. ia_influxdbconnector service must be running in order for grafana to collect time series data.
4. Once the data source is working, we can visualize the incoming data using the preconfigured dashboard. We can aslo edit the dashboard as per our convenience.

# CONFIGURATION #

1. [dashboard.json](./dashboard.json)
    This is the dashboard json file that is loaded when grafana starts. It has been preconfigured to display time-series data. 

2. [dashboard_sample.yml](./dashboard_sample.yml)
    This is the config file for all the dashboards. It specifies the path where all the dashboard json files will be looked for.

3. [datasource_sample.yml](./datasource_sample.yml)
    This is the config file for setting up the datasource. It has got various fields for datasource configuration.

4. [grafana_template.ini](./grafana_template.ini)
    This is the config for Grafana itself. It specifies how grafana should start up, once it has been configured.

NOTE: The contents of these files can be edited according to the requirement.

# PROCEDURE TO RUN GRAFANA (DEFAULT: PROD MODE) #

1. Open [docker-compose.yml](/docker_setup/docker-compose.yml) and uncomment ia_grafana.
2. Check ia_influxdbconnector, ia_data_analytics, ia_telegraph are running for time-series data.
3. Check [publisher](/tools/mqtt-temp-sensor/publisher.sh) is running.
4. Use "docker-compose build" to build image.
5. Use "docker-compose up" to run the service.
6. Once ia_grafana service is up, go to https://localhost:3000 (for PROD_MODE) and http://localhost:3000 (for DEV_MODE).
7. Provide default username: "admin" and password: "admin".
8. On successful login you will be routed on to the grafana "Home Dashboard" page.

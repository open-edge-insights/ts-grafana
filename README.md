# Grafana

1. Grafana is an open source metric analytics & visualization suite. It is most commonly used for visualizing time series data for infrastructure and        application analytics but many use it in other domains including industrial sensors, home automation, weather, and process control.
2. Grafana supports many different storage backends for our time series data (Data Source). Here in EII we are using InfluxDB as datasource.
3. Grafana connects to the InfluxDB datasource which has been preconfigured as a part of grafana setup. The data source i.e. ia_influxdbconnector service must be running in order for grafana to collect time series data.
4. Once the data source is working, we can visualize the incoming data using the preconfigured dashboard. We can aslo edit the dashboard as per our convenience.

## Configuration

1. [dashboard.json](./dashboard.json)
    This is the dashboard json file that is loaded when grafana starts. It has been preconfigured to display time-series data.

2. [dashboard_sample.yml](./dashboard_sample.yml)
    This is the config file for all the dashboards. It specifies the path where all the dashboard json files will be looked for.

3. [datasource_sample.yml](./datasource_sample.yml)
    This is the config file for setting up the datasource. It has got various fields for datasource configuration.

4. [grafana_template.ini](./grafana_template.ini)
    This is the config for Grafana itself. It specifies how grafana should start up, once it has been configured.

NOTE: The contents of these files can be edited according to the requirement.

## Procedure to run Grafana

1. Open [docker-compose.yml](/build/docker-compose.yml) and uncomment ia_grafana.
2. Check ia_influxdbconnector, ia_kapacitor, ia_telegraph are running for time-series data.
3. Check [publisher](https://github.com/open-edge-insights/eii-tools/blob/master/mqtt-publisher/publisher_temp.sh) is running.
4. Use "docker-compose build" to build image.
5. Use "docker-compose up" to run the service.

* **Prod mode [To be followed when running in PROD mode, skip if DEV mode]**

    Import 'cacert.pem' from 'build/Certificates/rootca/' Directory to your Browser Certifcates.

    Steps to Import Certificates
  * Go to *Settings* in Chrome
  * Search *Manage Certificates* Under Privacy & Security
  * Select Manage Certificates Option
  * Under *Authorities* Tab Click Import Button
  * With Import Wizard navigate to
        *IEdgeInsights/build/Certificates/rootca/* Dir
  * Select *cacert.pem* file
  * Select All CheckBoxes and Click Import Button.
* **Dev mode [To be followed when running in DEV mode]**

6. Once ia_grafana service is up, go to http://< host ip >:3000 .
7. Provide default username: "admin" and password: "admin".
8. On "Home Dashboard" page, click on Dashboards icon from the left corner.
9. Click on Manage Dashboards tab, it will list out all the preconfigured dashboards.
10. Click on "Point_Data_Dashboard" which is a preconfigured dashboard.
11. Click on "Panel Title" and select the "edit" option.
12. Now you will be on Point_Data_Dashboard page and here you can make modifications to the query.

## Steps to execute query

1. Once landed on the `Point_Data_Dashboard`, green spikes visible in the
   graph are the results of the default query

2. In the "FROM" section of query, by default it will have 'default
   point_classifier_results WHERE +',
   click on 'default_classifier_results', drop down will open with the name of Measurements present in InfluxDB.
   If any other measurement is set the graph will switch to the measurement query results.

3. In the "SELECT" section, by default it will have 'field(temperature) mean() +'. Click on 'temperature', a drop down will
   open with the fields tags present in the schema of the measurements set in the FROM section.
   Select any options the graph will react accordingly.

## Steps for running Grafana in video usecase

1. Ensure the endpoint of the publisher you want to subscribe to is mentioned in **Subscribers** section of
   [config](config.json)

2. On "Home Dashboard" page, click on Dashboards icon from the left corner.
   Click on Manage Dashboards tab, it will list out all the preconfigured dashboards.

3. Select **EII Video and Time Series Dashboard**, you would be able to view multiple panels with topic names of the subscriber
   as the panel names along with a time-series panel named Time Series.

4. Hovering over the topic name, i.e, panel title will display multiple options, one of them being View.

5. Click on View and you should be able to view the subscribed frames for each topic.

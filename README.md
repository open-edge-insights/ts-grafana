# Grafana

Grafana is an open-source metric analytics and visualization suite. Its uses include:

- Visualizing time series data for infrastructure and application analytics
- Industrial sensors, home automation, weather, and process control

Grafana supports various storage backends for the time-series data (data source). Open Edge Insights (OEI) uses InfluxDB as the data source. Grafana connects to the InfluxDB data source which has been preconfigured as a part of the Grafana setup. The 'ia_influxdbconnector' service must be running for Grafana to be able to collect the time-series data. After the data source starts working, you can use the preconfigured dashboard to visualize the incoming data. You can also edit the dashboard as required.

## Configuration

The following are the configuration details for Grafana:

- [dashboard.json](./dashboard.json): This is the dashboard json file that is loaded when Grafana starts. It is preconfigured to display the time-series data.

- [dashboard_sample.yml](./dashboard_sample.yml): This is the config file for all the dashboards. It specifies the path to locate all the dashboard json files.

- [datasource_sample.yml](./datasource_sample.yml): This is the config file for setting up the data source. It has various fields for data source configuration.

- [grafana_template.ini](./grafana_template.ini): This is the config file for Grafana. It specifies how Grafana should start after it is configured.

>**Note:** You can edit the contents of these files based on your requirement.

## Run Grafana

Based on requirement, you can run Grafana in the `Prod mode` or the `DEV mode`.

Complete the following steps to run Grafana:

1. Open the [docker-compose.yml](/build/docker-compose.yml) file.
2. In the `docker-compose.yml`, uncomment ia_grafana.
3. Check if the `ia_influxdbconnector`, `ia_kapacitor`, and `ia_telegraph` services are running for the time-series data.
4. Check if the [publisher](https://github.com/open-edge-insights/eii-tools/blob/master/mqtt-publisher/publisher_temp.sh) service is running.
5. Run the `docker-compose build` command to build image.
6. Run the `docker-compose up` to start the service.

Complete the previous steps and based on the mode that you want to run Grafana refer to the following sections:

### Run Grafana in the PROD mode

>**Note:** Skip this section, if you are running Grafana in the DEV mode.

To run Grafana in the PROD mode, import `cacert.pem` from the `build/Certificates/rootca/` directory to the browser certificates. Complete the following steps to import certificates:

1. In Chrome browser, go to **Settings**.
2. In **Search settings**, enter **Manage certificates**.
3. Click **Security**.
4. On the **Advanced** section, click **Manage certificates**.
5. On the **Certificates** window, click the **Trusted Root Certification Authorities** tab.
6. Click **Import**.
7. On the **Certificate Import Wizard**, click **Next**.
8. Click **Browse**.
9. Go to the `IEdgeInsights/build/Certificates/rootca/` directory.
10. Select the **cacert.pem** file.
11. Select all checkboxes and then, click **Import**.

### Run Grafana in the DEV mode

To run Grafana in the PROD mode, complete the following steps:

1. After starting the `ia_grafana` service, go to `http://< host ip >:3000`.
2. Enter the default credentials details, username: "admin" and password: "admin".
3. On the **Home Dashboard** page, on the left corner, click the Dashboards icon.
4. Click the **Manage Dashboards** tab.
5. From the list of preconfigured dashboards, click **Point_Data_Dashboard**.
6. Click **Panel Title** and then, select **Edit**.
7. On the **Point_Data_Dashboard** page, if required make modifications to the query.

## Execute queries

On the `Point_Data_Dashboard`, the green spikes visible in the graph are the results of the default query. To run queries, perform the following steps:

1. In the **FROM** section of query, click **default_classifier_results**. A list is displayed with the name of measurements present in InfluxDB.
   >**Note:** If any other measurement is set the graph will switch to the measurement query results.
   > By default, the **FROM** section will have **default point_classifier_results WHERE +**.

2. In the **SELECT** section, click **temperature**. A list will display the fields tags present in the schema of the measurements set in the **FROM** section.
   >**Note:** By default the **SELECT** section will have **field(temperature) mean() +**.
   > The graph will change according to the values you select.

## Run Grafana for video use cases

Perform the following steps to run Grafana for a video use case:

1. Ensure that the endpoint of the publisher, that you want to subscribe to, is mentioned in the **Subscribers** section of the [config](config.json) file.
2. On the **Home Dashboard** page, on the left corner, click the Dashboards icon.
3. Click the **Manage Dashboards** tab, to view the list of all the preconfigured dashboards.
4. Select **EII Video and Time Series Dashboard**, to view multiple panels with topic names of the subscriber as the panel names along with a time-series panel named `Time Series`.
5. Hover over the topic name. The panel title will display multiple options.
6. Click **View** to view the subscribed frames for each topic.

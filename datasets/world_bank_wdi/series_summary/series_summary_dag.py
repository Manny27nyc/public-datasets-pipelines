# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from airflow import DAG
from airflow.contrib.operators import gcs_to_bq, kubernetes_pod_operator

default_args = {
    "owner": "Google",
    "depends_on_past": False,
    "start_date": "2021-03-01",
}


with DAG(
    dag_id="world_bank_wdi.series_summary",
    default_args=default_args,
    max_active_runs=1,
    schedule_interval="@daily",
    catchup=False,
    default_view="graph",
) as dag:

    # Run CSV transform within kubernetes pod
    series_summary_transform_csv = kubernetes_pod_operator.KubernetesPodOperator(
        task_id="series_summary_transform_csv",
        startup_timeout_seconds=600,
        name="series_summary",
        namespace="composer",
        service_account_name="datasets",
        image_pull_policy="Always",
        image="{{ var.json.world_bank_wdi.container_registry.run_csv_transform_kub }}",
        env_vars={
            "SOURCE_URL": "gs://pdp-feeds-staging/RelayWorldBank/WDI_csv/WDISeries.csv",
            "SOURCE_FILE": "files/data.csv",
            "COLUMN_TO_REMOVE": "Unnamed: 20",
            "TARGET_FILE": "files/data_output.csv",
            "TARGET_GCS_BUCKET": "{{ var.value.composer_bucket }}",
            "TARGET_GCS_PATH": "data/world_bank_wdi/series_summary/data_output.csv",
            "PIPELINE_NAME": "series_summary",
            "CSV_HEADERS": '["series_code","topic","indicator_name","short_definition","long_definition","unit_of_measure","periodicity","base_period","other_notes","aggregation_method","limitations_and_exceptions","notes_from_original_source","general_comments","source","statistical_concept_and_methodology","development_relevance","related_source_links","other_web_links","related_indicators","license_type"]',
            "RENAME_MAPPINGS": '{"Series Code":"series_code","Topic":"topic","Indicator Name":"indicator_name","Short definition":"short_definition","Long definition":"long_definition","Unit of measure":"unit_of_measure","Periodicity":"periodicity","Base Period":"base_period","Other notes":"other_notes","Aggregation method":"aggregation_method","Limitations and exceptions":"limitations_and_exceptions","Notes from original source":"notes_from_original_source","General comments":"general_comments","Source":"source","Statistical concept and methodology":"statistical_concept_and_methodology","Development relevance":"development_relevance","Related source links":"related_source_links","Other web links":"other_web_links","Related indicators":"related_indicators","License Type":"license_type"}',
        },
        resources={"request_memory": "2G", "request_cpu": "1"},
    )

    # Task to load CSV data to a BigQuery table
    load_series_summary_to_bq = gcs_to_bq.GoogleCloudStorageToBigQueryOperator(
        task_id="load_series_summary_to_bq",
        bucket="{{ var.value.composer_bucket }}",
        source_objects=["data/world_bank_wdi/series_summary/data_output.csv"],
        source_format="CSV",
        destination_project_dataset_table="world_bank_wdi.series_summary",
        skip_leading_rows=1,
        allow_quoted_newlines=True,
        write_disposition="WRITE_TRUNCATE",
        schema_fields=[
            {
                "name": "series_code",
                "type": "string",
                "description": "A number or a sequence of related statistical units arranged or occurring in temporal spatial or other order or succession. WDI carries mostly time series.",
                "mode": "nullable",
            },
            {
                "name": "topic",
                "type": "string",
                "description": "The matter dealt with in the context discourse or subject related to the series.",
                "mode": "nullable",
            },
            {
                "name": "indicator_name",
                "type": "string",
                "description": "Given name of a series.",
                "mode": "nullable",
            },
            {
                "name": "short_definition",
                "type": "string",
                "description": "Short statement of the exact meaning of a series.",
                "mode": "nullable",
            },
            {
                "name": "long_definition",
                "type": "string",
                "description": "Extended statement of the exact meaning of a series.",
                "mode": "nullable",
            },
            {
                "name": "unit_of_measure",
                "type": "string",
                "description": "A quantity used as a standard of measurement. Example: Units of time are second minute hour day week month year and decade.",
                "mode": "nullable",
            },
            {
                "name": "periodicity",
                "type": "string",
                "description": "Applies to series recurring at regular intervals. Most of the time this term denotes that interval of recurrence.",
                "mode": "nullable",
            },
            {
                "name": "base_period",
                "type": "string",
                "description": "Base period is the period of time for which data is used as the base of an index number or other ratio have been collected. This period is frequently one of a year but it may be as short as one day or as long as the average of a group of years.",
                "mode": "nullable",
            },
            {
                "name": "other_notes",
                "type": "string",
                "description": "A brief record of facts topics or thoughts written down and used to contextualize the series definition values and other characteristics.",
                "mode": "nullable",
            },
            {
                "name": "aggregation_method",
                "type": "string",
                "description": "Aggregation methods are types of calculations used to group attribute values into a metric for each dimension value. For example for each region one may retrieve the total value of country entries (the sum of the series value for countries belonging to the region).",
                "mode": "nullable",
            },
            {
                "name": "limitations_and_exceptions",
                "type": "string",
                "description": "A limiting rule or circumstance that applies to usage of the series such as the scope of the survey collecting the data or missing years and countries.  It should also note when data are imputed or estimated",
                "mode": "nullable",
            },
            {
                "name": "notes_from_original_source",
                "type": "string",
                "description": "A brief record of facts topics or thoughts written down and used to contextualize the series definition values and other characteristics.",
                "mode": "nullable",
            },
            {
                "name": "general_comments",
                "type": "string",
                "description": "Other notes regarding the series which do not appear in Development relevance or Limitations or exceptions",
                "mode": "nullable",
            },
            {
                "name": "source",
                "type": "string",
                "description": "A place person or organization from which the series comes or can be obtained.",
                "mode": "nullable",
            },
            {
                "name": "statistical_concept_and_methodology",
                "type": "string",
                "description": "The abstract idea general statistical notions or a system of methods used to generate the series.",
                "mode": "nullable",
            },
            {
                "name": "development_relevance",
                "type": "string",
                "description": "The relevance of a series refers to how the indicator’s data may be used to monitor particular aspects of development goals and programs for example the Sustainable Development Goals. The indicator may conclusively measure progress towards a particular objective or may act as a proxy or interpretation of a development aim.",
                "mode": "nullable",
            },
            {
                "name": "related_source_links",
                "type": "string",
                "description": "Internet address of related source page tool or knowledge base.",
                "mode": "nullable",
            },
            {
                "name": "other_web_links",
                "type": "string",
                "description": "Internet addresses of related pages tools or knowledge bases.",
                "mode": "nullable",
            },
            {
                "name": "related_indicators",
                "type": "string",
                "description": "In general indicator that are of interest and related to the specific series.",
                "mode": "nullable",
            },
            {
                "name": "license_type",
                "type": "string",
                "description": "Explains the rights conferred and restrictions imposed by the owner to the users of a series",
                "mode": "nullable",
            },
        ],
    )

    series_summary_transform_csv >> load_series_summary_to_bq

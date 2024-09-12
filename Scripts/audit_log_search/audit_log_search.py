import oci
import datetime

SEARCH_QUERY="search \"ocid1.compartment.oc1..aaaaaaa/_Audit\" | (type='com.oraclecloud.ComputeApi.DeleteImage')"

ENDTIME=datetime.datetime(2023, 11, 1, tzinfo=datetime.timezone.utc)

config = oci.config.from_file()
tenancy_id = config['tenancy']
loggingsearch_client = oci.loggingsearch.LogSearchClient(config)

search_time_end=datetime.datetime.now(datetime.timezone.utc)
search_time_start= search_time_end - datetime.timedelta(days=14)


while search_time_start > ENDTIME:
        print("Searching two weeks from: " + search_time_end.isoformat("T","seconds"))
        search_response = loggingsearch_client.search_logs(
                search_logs_details=oci.loggingsearch.models.SearchLogsDetails(
                        search_query=SEARCH_QUERY,
                        time_start=search_time_start.isoformat("T","seconds"),
                        time_end=search_time_end.isoformat("T","seconds")
                )
        )
        if len(search_response.data.results) > 0:
                print(search_response.data.results)

        search_time_end = search_time_start
        search_time_start= search_time_end - datetime.timedelta(days=14)
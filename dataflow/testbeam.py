import os
import apache_beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.typehints import with_input_types
from apache_beam.typehints import with_output_types
from apache_beam.typehints import Any
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import StandardOptions
from apache_beam.io.textio import ReadFromText, WriteToText


class Split(apache_beam.DoFn):

    def process(self, element):
        """
        Splits each row on commas and returns a dictionary representing the
        row
        """
        picid, seq_img_id, ord_idx, pixel_val = element.split(",")

        return [{
            'picid': picid,
            'seq_img_id': seq_img_id,
            'ord_idx': ord_idx,
            'pixel_val': float(pixel_val)
        }]


class CollectPixelVals(apache_beam.DoFn):

    def process(self, element):
        """
        Returns a list of tuples containing picid and pixel_val
        """

        result = [
            ((element['picid'], element['seq_img_id'], element['ord_idx']), element['pixel_val'])
        ]
        return result


@with_input_types(Any)
@with_output_types(int)
class SumCombineFn(apache_beam.transforms.core.CombineFn):
    """CombineFn for computing PCollection size."""

    def create_accumulator(self):
        return 0  # Sum

    def add_input(self, current_sum, new_value):
        return current_sum + new_value

    def merge_accumulators(self, accumulators):
        return sum(accumulators)

    def extract_output(self, accumulator):
        return accumulator

class GetNormal(apache_beam.DoFn):

    def process(self, element):
        """
        Normalizes
        """
        idx = element[0]
        stamps, sums = element[1]

        result = stamps[0][0] / sums[0][0]
        return [(idx), result]

class WriteToCSV(apache_beam.DoFn):

    def process(self, element):
        """
        Prepares each row to be written in the csv
        """

        idx = element[0]
        data = element[1]

        result = '{},{}'.format(idx, data)
        return [result]


input_filename = 'gs://panoptes-test-bucket/PAN001_14d3bd_20190228T054237.csv'
output_filename = 'gs://panoptes-test-bucket/dataflow/output.txt'

# project_id = os.environ['DATASTORE_PROJECT_ID']
# credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
# client = datastore.Client.from_service_account_json(credentials_file)

options = PipelineOptions()
gcloud_options = options.view_as(GoogleCloudOptions)
# gcloud_options.project = project_id
gcloud_options.job_name = 'test-job'

# Dataflow runner
runner = os.getenv('DATAFLOW_RUNNER', 'DataFlowRunner')
options.view_as(StandardOptions).runner = runner

with apache_beam.Pipeline(options=options) as p:
    stamps = (
        p |
        "Reading CSV" >> ReadFromText(input_filename, skip_header_lines=1) |
        "Parsing CSV" >> apache_beam.ParDo(Split()) |
        "Getting stamps" >> apache_beam.ParDo(CollectPixelVals())
    )

    psc_collection = (
        stamps |
        "Making PSCs" >> apache_beam.GroupByKey()
    )

    # calculate the mean for Open values
    stamp_sums = (
        psc_collection |
        "Getting stamp sum" >> apache_beam.CombineValues(
            SumCombineFn()
        )
    )

    #normalized = (
    #    {
    #        'stamps': stamps,
    #        'sums': stamp_sums,
    #    } |
    #    "Grouping together" >> apache_beam.CoGroupByKey() |
    #    "NormalizingFlux" >> apache_beam.ParDo(GetNormal())
    #    )
#
    #results = (
    #    normalized |
    #    "Getting normal PSC" >> apache_beam.GroupByKey()
    #)

    output = (
        stamp_sums |
        "Formatting CSV" >> apache_beam.ParDo(WriteToCSV()) |
        "Writing CSV" >> WriteToText(output_filename)
    )

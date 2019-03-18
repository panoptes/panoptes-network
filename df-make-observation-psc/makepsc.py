from __future__ import absolute_import

import sys
import logging
import numpy as np
import pandas as pd

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.metrics import Metrics
from apache_beam.pvalue import TaggedOutput
from apache_beam.pvalue import AsIter, AsList
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


class SplitCSV(beam.DoFn):
    def __init__(self):
        self.total_invalid = Metrics.counter(self.__class__, 'total_invalid')

    def process(self, element):
        """
        Splits each row on commas and returns a dictionary representing the
        row
        """
        try:
            row_values = element.split(",")

            data = np.array(row_values[5:]).astype(np.int)
            # norm_data = data / sum(data)

            # picid, unit_id, camera_id, sequence_time, image_time
            row = {
                'picid': row_values[0],
                'unit_id': row_values[1],
                'camera_id': row_values[2],
                'sequence_time': row_values[3],
                'image_time': row_values[4],
                'data': data,
                # 'norm': norm_data
            }

            return [row]
        except Exception as e:
            logging.info('Invalid row found: %s %s', str(e), element)
            self.total_invalid.inc(1)


def make_key(row):
    return (row['picid'], row['unit_id'], row['camera_id'], row['sequence_time'])


class MaxFrames(beam.transforms.core.CombineFn):
    """CombineFn for computing PCollection size."""

    def create_accumulator(self):
        return 0  # max_frames

    def add_input(self, current_max, new_row):
        return max(current_max, new_row[1])

    def merge_accumulators(self, accumulators):
        return max(accumulators)

    def extract_output(self, accumulator):
        return accumulator


class ProcessPICID(beam.PTransform):
    def expand(self, pcoll):

        # norms = pcoll | 'Get norms' >> beam.Map(
        #     lambda row: (row['picid'], row['image_time'],
        #                  ','.join(row['norm'].flatten().astype(str).tolist()))
        # )

        # pscs = pcoll | 'Get data' >> beam.Map(
        #     lambda row: (row['picid'], row['image_time'],
        #                  ','.join(row['data'].flatten().astype(str).tolist()))
        # )

        # num_pixels = 100

        # column_names = ['picid', 'image_time'] + \
        #     ['pixel_{:02d}'.format(i) for i in range(num_pixels)]
        # stamps_df = pd.DataFrame(data=list(norms))

        # scores = find_similar_sources(stamps_df)

        pscs = pcoll | 'Get row info' >> beam.Map(lambda row: row[1]['frames'])

        # Ungroup so we have one row per picid per frame.
        output = pscs | 'Unroll PSCs' >> beam.ParDo(BreakRows())

        return output


def find_similar_sources(stamps_df):
    # Normalize each stamp
    norm_df = stamps_df.copy().apply(lambda x: x / stamps_df.sum(axis=1))

    top_matches = dict()
    for picid, row in norm_df.groupby('picid'):
        norm_target = row.droplevel('picid')
        norm_group = ((norm_df - norm_target)**2).dropna().sum(axis=1).groupby('picid')
        top_matches[picid] = norm_group.sum().sort_values()

    similar_sources = pd.DataFrame(top_matches)

    return similar_sources


class BreakRows(beam.DoFn):
    def process(self, element):
        key = element[0]
        frames = element[1]

        for row in frames:
            data = row.pop('data')
            key = tuple(row.values())
            yield (key, data)


class FormatPSCCSV(beam.DoFn):

    def process(self, element):
        """
        Prepares each row to be written in the csv
        """

        idx = element[0]
        data = element[1]
        try:
            data = data.astype(str)
        except AttributeError:
            pass

        result = '{},{},{}'.format(idx[0], idx[-1], ','.join(data))
        return [result]


class FormatScoresCSV(beam.DoFn):

    def process(self, element):
        """
        Prepares each row to be written in the csv
        """

        idx = element[0]
        data = element[1]
        try:
            data = data.astype(str)
        except AttributeError:
            pass

        result = '{},{},{}'.format(idx[0], idx[-1], ','.join(data))
        return [result]


def run(argv=None):
    """
    Main entry point; defines and runs the pipeline.
    """
    class PSCOptions(PipelineOptions):
        @classmethod
        def _add_argparse_args(cls, parser):
            # Use add_value_provider_argument for arguments to be templatable
            # Use add_argument as usual for non-templatable arguments
            parser.add_value_provider_argument(
                '--input', type=str,
                default='gs://panoptes-detected-sources/PAN012/358d0f/20180822T035809/*.csv',
                help='Sequence ID to process.')
            parser.add_value_provider_argument(
                '--pscs_output', type=str,
                default='gs://panoptes-observation-psc/PAN012/358d0f/20180822T035809.csv',
                help='Sequence ID to process.')
            parser.add_value_provider_argument(
                '--scores_output', type=str,
                default='gs://panoptes-observation-psc/PAN012/358d0f/20180822T035809-scores.csv',
                help='Sequence ID to process.')
            parser.add_value_provider_argument(
                '--frameThreshold', type=float, default=0.98,
                help='Percentage of frames that sources should be detected in')

    # Create and set your PipelineOptions.
    pipeline_options = PipelineOptions(flags=argv)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    psc_options = pipeline_options.view_as(PSCOptions)

    frame_threshold = 1.0  # psc_options.frameThreshold

    # Start pipeline
    with beam.Pipeline(options=pipeline_options) as p:
        # Read the json data and extract the datapoints.
        records = (p |
                   'Read source files' >> ReadFromText(psc_options.input, skip_header_lines=1)
                   # 'Parse row' >> beam.ParDo(SplitCSV())
                   )

        # Records keyed by picid but containing all info.
        # keyed_records = records | 'AddRowByKey' >> beam.Map(lambda row: ((row['picid']), row))

        # Count number of stamps for each picid.
        # picid_counts = keyed_records | 'Counting PICID' >> beam.combiners.Count.PerKey()

        # Singular value to get number of frames.
        # max_frames = beam.pvalue.AsSingleton(
        # picid_counts | 'Get Total Num Frames' >> beam.CombineGlobally(MaxFrames()))

        # Group by PICID.
        # picids = {'frames': keyed_records,
        # 'counts': picid_counts} | 'Combining Counts & Data' >> beam.CoGroupByKey()

        # Filter PICIDs that aren't in enough frames.
        # filtered = (
        #     picids |
        #     'Filter PICID' >> beam.Filter(lambda row, frame_count: int(
        #         row[1]['counts'][0]) >= int(frame_count * frame_threshold), max_frames) |
        #     'Clean Filtered' >> beam.Map(lambda row: [r for r in row])
        # )

        # Process the PICID.
        # output = (filtered | 'Process PICID' >> ProcessPICID())

        # Format for output
        # formatted_pscs = records | 'Formatting PSC CSV' >> beam.ParDo(FormatPSCCSV())
        # formatted_scores = scores | 'Formatting Scores CSV' >> beam.ParDo(FormatScoresCSV())

        # Write to file
        records | "Writing PSCs CSV" >> beam.io.WriteToText(
            psc_options.pscs_output, num_shards=1, shard_name_template='')
        # formatted_scores | "Writing scores CSV" >> beam.io.WriteToText(
        # self.scores_output, num_shards=1, shard_name_template='')

        # Actually run the pipeline (all operations above are deferred).
        result = p.run()
        result.wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run(sys.argv)

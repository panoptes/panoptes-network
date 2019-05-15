from __future__ import absolute_import

import sys
import logging

import apache_beam as beam
from apache_beam.io import ReadFromText
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


class SplitCSV(beam.DoFn):
    def process(self, element):
        cols = element.split(',')

        # picid[0], image_time[4], pixel_data[5:]
        return [[cols[0]] + cols[4:]]


class FormatPSCCSV(beam.DoFn):

    def process(self, element):
        """
        Prepares each row to be written in the csv
        """
        return [','.join(element)]


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

    # Create and set your PipelineOptions.
    pipeline_options = PipelineOptions(flags=argv)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    psc_options = pipeline_options.view_as(PSCOptions)

    num_pixels = 100  # WARNING
    header = 'picid,image_time,' + ','.join(['pixel_{:02d}'.format(i) for i in range(num_pixels)])

    # Start pipeline
    with beam.Pipeline(options=pipeline_options) as p:
        # Read the json data and extract the datapoints.
        (p |
         'Read source files' >> ReadFromText(
             psc_options.input,
             skip_header_lines=1) |
         'Parse row' >> beam.ParDo(SplitCSV()) |
         'Formatting PSC CSV' >> beam.ParDo(FormatPSCCSV()) |
         'Writing PSCs CSV' >> beam.io.WriteToText(
             psc_options.pscs_output,
             header=header,
             num_shards=1,
             shard_name_template='')
         )

        # Actually run the pipeline (all operations above are deferred).
        result = p.run()
        result.wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run(sys.argv)

#!/usr/bin/env python

import subprocess
import shutil
import re

from halo import Halo
from panoptes_utils.serializers import to_yaml
from panoptes_utils.serializers import from_yaml

kube_fn = 'similar-source-finder-deployment.yaml'


def main(container_name='gcr.io/panoptes-survey/find-similar-sources', timeout=1500):

    print(f'Container Name: {container_name}')

    # Get the gcloud command.
    gcloud_cmd = shutil.which('gcloud')
    gcloud_build_cmd = [gcloud_cmd, 'builds', 'submit']

    # Make entire command.
    build_cmd = gcloud_build_cmd + ['--timeout', str(timeout), '--tag', container_name]

    with Halo(spinner='dots') as spinner:
        spinner.text = 'Running build command'
        spinner.start()

        # Run the process and wait for output.
        completed_proc = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        spinner.succeed()

        spinner.text = 'Extracting SHA'
        spinner.start()
        # Look for the SHA digest.
        sha_re_text = 'latest: digest: sha256:(.*?) size:'
        matches = re.search(sha_re_text, completed_proc.stdout.decode('ascii'))
        if matches is None:
            spinner.fail()
            return
        else:
            sha256 = matches.group(1)
            spinner.succeed()

        spinner.text = 'Updating Kubernetes deployment yaml'
        spinner.start()
        try:
            # Get existing config
            with open(kube_fn, 'r') as f:
                kube_config = from_yaml(f.read())

            # Set new sha on image name.
            new_image = f'{container_name}@sha256:{sha256}'
            kube_config['spec']['template']['spec']['containers'][0]['image'] = new_image

            # Write new config.
            with open(kube_fn, 'w') as f:
                f.write(to_yaml(kube_config))

            spinner.succeed()
        except Exception as e:
            spinner.fail()
            print(e)
            return


if __name__ == '__main__':
    print("Docker GCE instance to find similar sources for each PSC in an observation.")
    main()

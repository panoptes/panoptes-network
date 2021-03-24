import os
from contextlib import suppress

from dateutil.parser import parse as parse_date
from google.cloud import firestore

firestore_db = firestore.Client()

STATS_FS_KEY = os.getenv('STATS_FS_KEY', 'stats')
UNITS_FS_KEY = os.getenv('UNITS_FS_KEY', 'units')
OBSERVATION_FS_KEY = os.getenv('OBSERVATION_FS_KEY', 'observations')
IMAGE_FS_KEY = os.getenv('OBSERVATION_FS_KEY', 'images')


def observations_entry(data, context):
    """ Triggered by an observation creation or deletion.

    This will update aggregation stats for `observations` based on whether
    the record was created or deleted.

    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    trigger_resource = context.resource
    sequence_id = trigger_resource.split('/')[-1]

    unit_id, camera_id, sequence_time = sequence_id.split('_')
    sequence_time = parse_date(sequence_time)

    # print(f'Change of {context.event_type} to sequence_id={sequence_id}')

    batch = firestore_db.batch()

    sequence_year, sequence_week, _ = sequence_time.isocalendar()

    # Firestore wants a tuple with a single entry.
    stat_week_key = (f'{STATS_FS_KEY}/{sequence_year}_{sequence_week:02d}_{unit_id}',)

    # Get the list of observation ids for the stat record associated with this observation.
    try:
        observations = firestore_db.document(stat_week_key).get([OBSERVATION_FS_KEY]).get(
            OBSERVATION_FS_KEY)
        print(f'Found existing observations: {observations!r}')
    except Exception as e:
        print(f'Unable to get firestore document: {e!r}')
        observations = list()

    num_observations = 0
    if context.event_type.endswith('create'):
        # Make sure no stats record exists and increment otherwise.
        if sequence_id in observations:
            print(f'{sequence_id} exists in {stat_week_key}, skipping create stats increment')
            return

        num_observations = firestore.Increment(1)
        obs_list_operation = firestore.ArrayUnion([sequence_id])
    elif context.event_type.endswith('delete'):
        # Find the stats record that matches and decrement if found.
        if sequence_id not in observations:
            print(
                f'{sequence_id} does not exist in {stat_week_key}, skipping delete stats decrement')
            return

        num_observations = firestore.Increment(-1)
        obs_list_operation = firestore.ArrayRemove([sequence_id])

    stats = {
        'year': sequence_year,
        'month': sequence_time.month,
        'week': sequence_week,
        'unit_id': unit_id,
        'num_observations': num_observations,
        'observations': obs_list_operation
    }
    counters = {'num_observations': num_observations}
    batch.set(firestore_db.document(stat_week_key), stats, merge=True)
    batch.set(firestore_db.document((f'{UNITS_FS_KEY}/{unit_id}',)), counters, merge=True)

    return batch.commit()


def images_entry(data, context):
    """ Triggered by an image creation or deletion.

    This will update aggregation stats for `images` based on whether
    the record was created or deleted.
    Args:
        data (dict): The event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    trigger_resource = context.resource
    image_id = trigger_resource.split('/')[-1]

    unit_id, camera_id, image_time = image_id.split('_')
    image_time = parse_date(image_time)

    # print(f'Change of {context.event_type} to image_id={image_id}')

    batch = firestore_db.batch()

    image_year, image_week, _ = image_time.isocalendar()

    stat_week_key = (f'{STATS_FS_KEY}/{image_year}_{image_week:02d}_{unit_id}',)

    exptime = 0  # Unknown
    mult = 1
    event_type = 'value'
    if context.event_type.endswith('delete'):
        event_type = 'oldValue'
        mult = -1

    with suppress(KeyError):
        exptime = mult * round(float(list(data[event_type]['fields']['exptime'].values())[0]))

    num_images = firestore.Increment(mult)
    exptime = firestore.Increment(round(exptime / 60, 2))  # Exptime as tenths of minutes.

    stats = {
        'year': image_year,
        'month': image_time.month,
        'week': image_week,
        'unit_id': unit_id,
        'num_images': num_images,
        'total_minutes_exptime': exptime,
    }
    counters = {'num_images': num_images, 'total_minutes_exptime': exptime}

    batch.set(firestore_db.document(stat_week_key), stats, merge=True)
    batch.set(firestore_db.document((f'{UNITS_FS_KEY}/{unit_id}',)), counters, merge=True)

    batch.commit()

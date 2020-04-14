from contextlib import suppress
from dateutil.parser import parse as parse_date

from google.cloud import firestore
firestore_db = firestore.Client()


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

    stat_week_key = f'stats/{sequence_year}_{sequence_week:02d}_{unit_id}'
    if context.event_type.endswith('create'):
        num_observations = firestore.Increment(1)
        obs_list_operation = firestore.ArrayUnion([sequence_id])
    elif context.event_type.endswith('delete'):
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
    batch.set(firestore_db.document(f'units/{unit_id}'), counters, merge=True)

    batch.commit()


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

    stat_week_key = f'stats/{image_year}_{image_week:02d}_{unit_id}'

    exptime = 0  # Unknown
    if context.event_type.endswith('create'):
        doc = data['value']
        mult = 1
    elif context.event_type.endswith('delete'):
        doc = data['oldValue']
        mult = -1

    with suppress(KeyError):
        exptime = mult * round(float(list(doc['fields']['exptime'].values())[0]))

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

    sequence_id = doc['fields']['sequence_id']['stringValue']
    batch.set(firestore_db.document(stat_week_key), stats, merge=True)
    batch.set(firestore_db.document(f'units/{unit_id}'), counters, merge=True)
    batch.set(firestore_db.document(f'observations/{sequence_id}'), counters, merge=True)

    batch.commit()

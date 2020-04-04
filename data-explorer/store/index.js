export const state = () => ({
  title: 'PANOPTES Data Explorer'
})

export const strict = false

export const formatFirestoreRow = (data) => {
  // console.log('Formatting row');
  // console.log(data);
  // Turn into a time object.
  if ('time' in data && data['time'] !== null) {
    data['time'] = data['time'].toDate().toUTCString()
  }

  // Don't return 9 digits of precision.
  if ('ra' in data && data['ra'] !== null) {
    data['ra'] = data['ra'].toFixed(3)
  }
  if ('dec' in data && data['dec'] !== null) {
    data['dec'] = data['dec'].toFixed(3)
  }

  if ('location' in data && data['location'] !== null) {
    data['latitude'] = data['location'].latitude
    data['longitude'] = data['location'].longitude
    delete data.location
  }

  return data
}

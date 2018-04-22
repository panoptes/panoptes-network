const { Pool, Client } = require('pg')
const Storage = require("@google-cloud/storage");

const projectId = 'panoptes-survey';
const bucketName = 'panoptes-test-bucket';

// Creates a client
const storage = new Storage({
  projectId: projectId,
});

const CloudSQLInstanceId = 'panoptes-survey:us-central1:panoptes-meta';
const pool = new Pool({
  user: 'postgres',
  password: 'pan0pt3&-m3t4',
  database: 'panoptes',
  host: '/cloudsql/' + CloudSQLInstanceId // https://issuetracker.google.com/issues/36388165#comment144
})


exports.testDB = (event, callback) => {
  const file = event.data;
  const context = event.context;

  storage.
    bucket(bucketName).
    file(file.name).
    download( function(err, contents) {
    	console.info(contents.substr(0, 2048));
    } );

  // callback - checkout a client
  pool.connect((err, client, done) => {
    if (err) throw err

    const text = 'INSERT INTO units(id, name) VALUES($1, $2) RETURNING *'
    const values = [8, 'BigMac']
    
    // callback
    client.query(text, values, (err, res) => {
      if (err) {
        console.log(err.stack)
      } else {
        console.log(res.rows[0])
      }
    })
  })

  console.log(`Event ${context.eventId}`);
  console.log(`  Event Type: ${context.eventType}`);
  console.log(`  Bucket: ${file.bucket}`);
  console.log(`  File: ${file.name}`);
  console.log(`  Metageneration: ${file.metageneration}`);
  console.log(`  Created: ${file.timeCreated}`);
  console.log(`  Updated: ${file.updated}`);

  callback();
};
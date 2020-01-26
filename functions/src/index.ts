import * as functions from 'firebase-functions';
const admin = require('firebase-admin');

// // Start writing Firebase Functions
// // https://firebase.google.com/docs/functions/typescript
//

admin.initializeApp({
  credential: admin.credential.applicationDefault()
});

const db = admin.firestore();
const increment = admin.firestore.FieldValue.increment(1);

exports.updateImageCounts = functions.firestore
    .document('images/{imageId}')
    .onCreate((snap, context) => {
      const newValue = snap.data();

      if (newValue !== undefined){
          // Get the unit_id from the image id.
          const unitId = context.params.imageId.split('_')[0];
          const observationId:string = newValue.sequence_id;

          if (observationId > '') {
            // Update image count for observations.
            const obsRef = db.collection('observations').doc(observationId);
            obsRef.update({ num_images: increment })
            .then(function() {
                  console.log('Unit image count updated');
              })
              .catch(function(error:any) {
                  console.error(error);
              });
              
              // Update image count for unit.
            const unitRef = db.collection('units').doc(unitId);
            unitRef.update({ num_images: increment })
            .then(function() {
                  console.log('Unit image count updated');
             })
             .catch(function(error:any) {
                  console.error(error);
             });
          } else {
            console.log('Image ID does not contain a valid unit_id');
          }
      }
    });

exports.updateObservationCounts = functions.firestore
    .document('observations/{observationId}')
    .onCreate((snap, context) => {
      const newValue = snap.data();

      if (newValue !== undefined){
          const unitId:string = newValue.unit_id;

          if (unitId > ''){
            // Update image count for unit.
            const unitRef = db.collection('units').doc(unitId);
            unitRef.update({ num_observations: increment })
            .then(function() {
                  console.log('Unit observation count updated');
             })
             .catch(function(error:any) {
                  console.error(error);
             });
          } else {
            console.log('Observation does not contain a valid unit_id');
          }
      }
    });    

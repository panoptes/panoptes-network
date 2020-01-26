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
          // access a particular field as you would any JS property
          const unitId = newValue.unit_id;
          const observationId = newValue.unit_id;
    
          // Update image count for observations.
          const obsRef = db.doc('observations/' + observationId);
          obsRef.update({ num_images: increment })
          .then(function() {
                console.log('Unit image count updated');
            })
            .catch(function(error:any) {
                console.error(error);
            });
            
            // Update image count for unit.
          const unitRef = db.doc('units/' + unitId);
          unitRef.update({ num_images: increment })
          .then(function() {
                console.log('Unit image count updated');
           })
           .catch(function(error:any) {
                console.error(error);
           });
      }

    });

exports.updateObservationCounts = functions.firestore
    .document('observations/{observationId}')
    .onCreate((snap, context) => {
      const newValue = snap.data();

      if (newValue !== undefined){
          // access a particular field as you would any JS property
          const unitId = newValue.unit_id;
    
          // Update image count for unit.
          const unitRef = db.doc('units/' + unitId);
          unitRef.update({ num_observations: increment })
          .then(function() {
                console.log('Unit observation count updated');
           })
           .catch(function(error:any) {
                console.error(error);
           });
      }

    });    

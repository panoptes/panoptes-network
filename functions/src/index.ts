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
const decrement = admin.firestore.FieldValue.increment(-1);


export const getUnits = functions.https.onCall((data, context) => {
  const units:any[] = [];
  db.collection("units").get()
  .then((querySnapshot:FirebaseFirestore.QuerySnapshot) => {
    querySnapshot.forEach((doc:FirebaseFirestore.QueryDocumentSnapshot) => {
        console.log(`${doc.id} => ${doc.data()}`);
        const unitData = doc.data();
        unitData['unit_id'] = doc.id;
        units.push(unitData);
    });
  })
  .catch((err:any) => {
    console.error(err);
  });
  return units;
 });


exports.imagesCountIncrement = functions.firestore
    .document('images/{imageId}')
    .onCreate((snap, context) => {
      // Get the unit_id from the image id.
      const unitId = context.params.imageId.split('_')[0];
      const observationId:string = snap.get('sequence_id');

      const unitRef = db.collection('units').doc(unitId);
      const obsRef = db.collection('observations').doc(observationId);
  
      db.runTransaction((transaction:any) => {
        transaction.get(unitRef).then(() => {
          transaction.update(unitRef, {
            num_images: increment,
          });
          transaction.update(obsRef, {
            num_images: increment,
          });          
        });
      })
      .then(() => console.log('Image count incremented') )
      .catch((err:any) => { console.log(err) });
    });

exports.imagesCountDecrement = functions.firestore
    .document('images/{imageId}')
    .onCreate((snap, context) => {
      // Get the unit_id from the image id.
      const unitId = context.params.imageId.split('_')[0];
      const observationId:string = snap.get('sequence_id');

      const unitRef = db.collection('units').doc(unitId);
      const obsRef = db.collection('observations').doc(observationId);
  
      db.runTransaction((transaction:any) => {
        transaction.get(unitRef).then(() => {
          transaction.update(unitRef, {
            num_images: decrement,
          });
          transaction.update(obsRef, {
            num_images: decrement,
          });          
        });
      })
      .then(() => console.log('Image count decremented') )
      .catch((err:any) => { console.log(err) });
    });    

exports.obsevationsCountIncrement = functions.firestore
  .document('observations/{observationId}')
  .onCreate((snap, context) => {
    // Get a reference to the unit
    const unitId:string = snap.get('unit_id');
    const unitRef = db.collection('units').doc(unitId);

    // Update aggregations in a transaction
    db.runTransaction((transaction:any) => {
      transaction.get(unitRef).then(() => {
        // increment count
        transaction.update(unitRef, {
          num_observations: increment,
        });
      });
    })
    .then(() => console.log('Observation count incremented') )
    .catch((err:any) => { console.log(err) });
  });

exports.obsevationsCountDecrement = functions.firestore
    .document('observations/{observationId}')
    .onDelete((snap, context) => {
      // Get a reference to the unit
      const unitId:string = snap.get('unit_id');
      const unitRef = db.collection('units').doc(unitId);

      // Update aggregations in a transaction
      db.runTransaction((transaction:any) => {
        transaction.get(unitRef).then(() => {
          // decrement count
          transaction.update(unitRef, {
            num_observations: decrement,
          });
        });
      })
      .then(() => console.log('Observation count decremented') )
      .catch((err:any) => { console.log(err) });
    });
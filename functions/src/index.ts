// Firebase App (the core Firebase SDK) is always required and
// must be listed before other Firebase SDKs
const firebase = require("firebase");
// Required for side-effects
require("firebase/firestore");
import * as functions from 'firebase-functions';

// Start writing Firebase Functions
// https://firebase.google.com/docs/functions/typescript

export const getUnits = functions.https.onCall((data:any, context:any) => {
    let units: object = {};
    db.collection("units").get().then((querySnapshot:any) => {
        querySnapshot.forEach((doc:any) => {
            units[doc.id] = doc.data();
        });
        return units;
    }).catch((err:any) => {
        return {'error': err};
    });
});


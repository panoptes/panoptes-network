import * as functions from 'firebase-functions'
import * as admin from 'firebase-admin'

admin.initializeApp({
  credential: admin.credential.applicationDefault()
})

const db = admin.firestore()
const increment = admin.firestore.FieldValue.increment(1)
const decrement = admin.firestore.FieldValue.increment(-1)

export const formatFirestoreRow = (data: any) => {
  console.log('Formatting row');
  console.log(data);
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

export const getRecentObservations = functions.https.onCall(async (data, context) => {
  let limit: number = 25
  if ('limit' in data) {
    limit = data.limit
  }
  const observationList: any[] = []
  try {
    const querySnapshot = await db.collection("observations").orderBy('time', 'desc').limit(limit).get()
    querySnapshot.forEach((doc: FirebaseFirestore.QueryDocumentSnapshot) => {
      const obsData = formatFirestoreRow(doc.data())
      obsData['sequence_id'] = doc.id
      observationList.push(obsData)
    })
    return observationList
  }
  catch (err) {
    console.error(err)
    return observationList
  }
})

export const getObservation = functions.https.onCall(async (data, context) => {
  const docRef = db.collection("observations").doc(data.sequence_id)
  return await docRef.get().then(function (doc) {
    if (doc.exists) {
      const docData = formatFirestoreRow(doc.data())
      if (docData !== undefined) {
        docData['sequence_id'] = doc.id
      }
      return docData
    } else {
      return {}
    }
  }).catch(function (error) {
    console.log("Error getting document:", error)
  })
})

export const getImages = functions.https.onCall(async (data, context) => {
  const imageList: any[] = []
  try {
    const querySnapshot = await db.collection("images").where("sequence_id", "==", data.sequence_id).orderBy('time', 'desc').get()
    querySnapshot.forEach((doc: FirebaseFirestore.QueryDocumentSnapshot) => {
      const imgData = formatFirestoreRow(doc.data())
      imgData['image_id'] = doc.id
      imageList.push(imgData)
    })
    return imageList
  }
  catch (err) {
    console.error(err)
    return imageList
  }
})

export const getRecentLightcurves = functions.https.onCall(async (data, context) => {
  let limit: number = 25
  if ('limit' in data) {
    limit = data.limit
  }
  const observationList: any[] = []
  try {
    const querySnapshot = await db.collection("lightcurves").orderBy('time', 'desc').limit(limit).get()
    querySnapshot.forEach((doc: FirebaseFirestore.QueryDocumentSnapshot) => {
      const obsData = formatFirestoreRow(doc.data())
      obsData['lightcurve_id'] = doc.id
      observationList.push(obsData)
    })
    return observationList
  }
  catch (err) {
    console.error(err)
    return observationList
  }
})

export const getUnits = functions.https.onCall(async (data, context) => {
  const units: any[] = []
  try {
    const querySnapshot = await db.collection("units").get()
    querySnapshot.forEach((doc: FirebaseFirestore.QueryDocumentSnapshot) => {
      const unitData = doc.data()
      unitData['unit_id'] = doc.id
      units.push(unitData)
    })
    return units
  }
  catch (err) {
    console.error(err)
    return units
  }
})

// export const imagesCountIncrement = functions.firestore
//   .document('images/{imageId}')
//   .onCreate((snap, context) => {
//     // Get the unit_id from the image id.
//     const unitId = context.params.imageId.split('_')[0]
//     const observationId: string = snap.get('sequence_id')

//     const unitRef = db.collection('units').doc(unitId)
//     const obsRef = db.collection('observations').doc(observationId)

//     return db.runTransaction((transaction) => {
//       return transaction.get(unitRef).then(() => {
//         transaction.update(unitRef, {
//           num_images: increment,
//         })
//         transaction.update(obsRef, {
//           num_images: increment,
//         })
//       }).catch((err) => {

//       })
//     })
//   })

// export const imagesCountDecrement = functions.firestore
//   .document('images/{imageId}')
//   .onDelete((snap, context) => {
//     // Get the unit_id from the image id.
//     const unitId = context.params.imageId.split('_')[0]
//     const observationId: string = snap.get('sequence_id')

//     const unitRef = db.collection('units').doc(unitId)
//     const obsRef = db.collection('observations').doc(observationId)

//     return db.runTransaction((transaction) => {
//       return transaction.get(unitRef).then(() => {
//         transaction.update(unitRef, {
//           num_images: decrement,
//         })
//         transaction.update(obsRef, {
//           num_images: decrement,
//         })
//       })
//     })
//   })

export const obsevationsCountIncrement = functions.firestore
  .document('observations/{observationId}')
  .onCreate((snap, context) => {
    // Get a reference to the unit
    const unitId: string = snap.get('unit_id')
    const unitRef = db.collection('units').doc(unitId)

    return db.runTransaction((transaction) => {
      return transaction.get(unitRef).then(() => {
        // increment count
        transaction.update(unitRef, {
          num_observations: increment,
        })
      })
    })
  })

export const obsevationsCountDecrement = functions.firestore
  .document('observations/{observationId}')
  .onDelete((snap, context) => {
    // Get a reference to the unit
    const unitId: string = snap.get('unit_id')
    const unitRef = db.collection('units').doc(unitId)

    return db.runTransaction((transaction) => {
      return transaction.get(unitRef).then(() => {
        // decrement count
        transaction.update(unitRef, {
          num_observations: decrement,
        })
      })
    })
  })

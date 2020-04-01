export const auth = firebase.auth()
export const DB = firebase.firestore()
export const Funcs = firebase.functions()
export const storage = firebase.storage()

//if (location.hostname === 'localhost') {
    //console.log('Localhost detected for firebase services.')
//  DB.settings({
//    host: 'localhost:8081',
//    ssl: false
//  })
    //Funcs.useFunctionsEmulator('http://localhost:5001')
//}

export default firebase



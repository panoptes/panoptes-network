export const state = () => ({
    title: "PANOPTES Data Explorer",
    model: {
        hasResults: false,
        modalActive: false,
        searchParams: {
            vmagRange: [8, 10],
            radiusUnits: ['Degree'],
            radiusUnit: 'Degree',
            searchRadius: 5,
            searchString: 'M42',
            ra: 83.822,
            dec: -5.931,
            startDate: null,
            endDate: null
        },
        selectedUnits: [],
        isSearching: {
            observations: false,
            images: false,
            stars: false,
            general: false
        },
        valid: false
    }
})

/**
 * Functions for saving form state to localstorage and retrieving and setting it
 */
define(function(require) {

    // Requires jQuery which is always required in NAV.

    function _getFormState(form) {
        // [{name: "name1", value: "value1"}, {name: "name2", value: "value1"}]
        // => { "name1": "value1", "name2": "value2"}
        return $(form).serializeArray().reduce(function(result, obj) {
            result[obj.name] = obj.value;
            return result;
        }, {});
    }

    function _setFormState(form, storageKey) {
        const state = _getFormStateFromStorage(storageKey) || {};
        Object.entries(state).forEach(function([key, value]) {
            form.elements[key].value = value;
        })
    }

    function _getFormStateFromStorage(storageKey) {
        return JSON.parse(localStorage.getItem(storageKey));
    }

    function _setFormStateInStorage(form, storageKey) {
        localStorage.setItem(storageKey, JSON.stringify(_getFormState(form)));
    }

    return {
        getFormState: _getFormState,
        getFormStateFromStorage: _getFormStateFromStorage,
        setFormState: _setFormState,
        setFormStateInStorage: _setFormStateInStorage,
    }

})

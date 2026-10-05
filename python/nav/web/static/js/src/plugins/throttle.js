define([], function () {
    /**
     * Returns a function that calls func at most once every wait
     * milliseconds. The first call runs immediately, unless options.leading
     * is false. Calls made while waiting are collapsed into one trailing call
     * with the latest arguments.
     *
     * Unlike underscore's _.throttle, which this replaces, func is called
     * without a `this`. Use an arrow function or bind() if func needs one.
     */
    function throttle(func, wait, options) {
        const leading = options?.leading !== false;
        let previous = 0;
        let timeout = null;
        let pendingArgs = null;

        function invoke(now) {
            previous = now;
            const args = pendingArgs;
            pendingArgs = null;
            func(...args);
        }

        function trailing() {
            timeout = null;
            invoke(leading ? Date.now() : 0);
        }

        return (...args) => {
            const now = Date.now();
            if (!previous && !leading) {
                previous = now;
            }
            const remaining = wait - (now - previous);
            pendingArgs = args;

            if (remaining <= 0 || remaining > wait) {
                if (timeout) {
                    clearTimeout(timeout);
                    timeout = null;
                }
                invoke(now);
            } else if (!timeout) {
                timeout = setTimeout(trailing, remaining);
            }
        };
    }

    return throttle;
});

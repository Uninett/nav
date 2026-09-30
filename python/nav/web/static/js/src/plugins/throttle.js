define([], function () {
    /**
     * Returns a function that calls func at most once every wait
     * milliseconds. The first call runs immediately, unless options.leading
     * is false. Calls made while waiting are collapsed into one trailing call
     * with the latest arguments.
     *
     * Replacement for underscore's _.throttle.
     */
    function throttle(func, wait, options) {
        const leading = !options || options.leading !== false;
        let previous = 0;
        let timeout = null;
        let pendingThis = null;
        let pendingArgs = null;

        function invoke(now) {
            previous = now;
            const context = pendingThis;
            const args = pendingArgs;
            pendingThis = pendingArgs = null;
            func.apply(context, args);
        }

        function trailing() {
            timeout = null;
            invoke(leading ? Date.now() : 0);
        }

        return function () {
            const now = Date.now();
            if (!previous && !leading) {
                previous = now;
            }
            const remaining = wait - (now - previous);
            pendingThis = this;
            pendingArgs = arguments;

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

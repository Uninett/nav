define([
    'libs/jquery'
], function () {

    var publicFunctions = {

        difference:   function (a, b, equality) {
            // Things that are in A and not in B
            // if A = {1, 2, 3, 4} and B = {2, 4, 6, 8}, then A - B = {1, 3}.
            var diff = [];

            /*
             ax = element in a (delta)
             bx = element in b (delta)
             x = list of elements
             b = list of elements
             */


            for (var i = 0; i < a.length; i++) {
                var ax = a[i];

                var isFound = false;
                for (var j = 0; j < b.length; j++) {
                    var bx = b[j];
                    isFound = equality(ax, bx);
                    if (isFound) {
                        // No need to traverse rest of b, if element ax is found in b
                        break;
                    }
                }
                if (!isFound) {
                    // push element from a if not found in list b
                    diff.push(ax);
                }
            }

            return diff;
        },
        intersection: function (a, b, equality) {
            // Things that are in A and in B
            // if A= {1, 2, 3, 4} and B = {2, 4, 5},
            // then A ∩ B = {2, 4}
            var intersection = [];

            /*
             ax = element in a
             bx = element in b
             a = list of elements
             b = list of elements
             */


            var lookupHelper = {};

            for (var i = 0; i < a.length; i++) {
                var ax = a[i];

                for (var j = 0; j < b.length; j++) {
                    var bx = b[j];
                    if (!!!lookupHelper[ax] && !!!lookupHelper[bx]) {
                        // neither element ax or element bx is in lookuphelper
                        // consider if bx should be added to intersection
                        if (equality(ax, bx)) {
                            // lookup helpers, hopefully makes us fast skip
                            // some elements from equality checking
                            lookupHelper[ax] = 1;
                            lookupHelper[bx] = 1;
                            // bx is is in a , storing it in intersection
                            intersection.push(bx);
                        }
                    }


                }
            }
            return intersection;
        }

    };

    return publicFunctions;
});

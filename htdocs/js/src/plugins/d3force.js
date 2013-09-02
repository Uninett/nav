define([
    'libs/jquery'
], function () {

    // nodes and links should be the same object instances
    // used in a D3.force layout algorithm!
    function NAVD3Force(nodes, links) {
        this.nodes = nodes;
        this.links = links;
    }

    NAVD3Force.prototype.addNode = function (id, data) {
        data.id = id;
        this.nodes.push(data);
        //update()
    };
    NAVD3Force.prototype.updateNode = function (node, data) {
        // node must be a node from this.nodes

        node.set(data.attributes, {'silent': true});
        if (!!data.position && !data.isDirty) {
            node.x = data.position.x;
            node.y = data.position.y;
            node.fixed = true;
        }
    };
    NAVD3Force.prototype.removeNode = function (id) {
        var i = 0;
        var n = this.findNode(id);
        while (i < this.links.length) {
            if ((this.links[i].source === n) || (this.links[i].target) === n) {
                this.links.splice(i, 1); // remove from links if found.
            } else {
                i++;
            }
        }
        this.nodes.splice(this.findNodeIndex(n.id), 1);
        //update()
    };
    NAVD3Force.prototype.removeLink = function (a, b) {
        var linkIndex = this.findLinkIndex(a, b);
        if (linkIndex) {
            this.links.splice(linkIndex, 1);
        }
        /// reassign indexes in this.nodes?
    };
    NAVD3Force.prototype.addLink = function (source, target, data) {
        function copyMeta(forceNode, newNode) {
            if (newNode.x) {
                forceNode.x = newNode.x;
            }
            if (newNode.y) {
                forceNode.y = newNode.y;
            }
            forceNode.data = newNode.data;
        }

        function getNode(x) {
            var xNode = null;
            if (_.isObject(x)) {
                xNode = this.findNode(x.id);
                if (!xNode) {
                    xNode = x;
                } else {
                    copyMeta(xNode, x);
                }
            } else {
                xNode = this.findNode(x);
            }
            return xNode;
        }

        var sourceNode = getNode.call(this, source);
        var targetNode = getNode.call(this, target);

        this.links.push({
            "source": sourceNode,
            "target": targetNode,
            "data":   data, "value": 1});

        //update()
    };
    NAVD3Force.prototype.findNode = function (id) {
        for (var i in this.nodes) {
            if (this.nodes[i].id === id) {
                return this.nodes[i];
            }
        }
        return null;
    };
    NAVD3Force.prototype.findNodeIndex = function (sysname) {
        for (var i in this.nodes) {
            if (this.nodes[i].id === sysname) {
                return i;
            }
        }
        return null;
    };
    NAVD3Force.prototype.findLink = function (sourceId, targetId) {

        var linkIndex = this.findLinkIndex(sourceId, targetId);
        if (linkIndex) {
            return this.links[linkIndex];
        }
        return null;
    };
    NAVD3Force.prototype.findLinkIndex = function (sourceId, targetId) {

        for (var i in this.links) {
            if ((this.links[i].source.id === sourceId) && (this.links[i].target.id === targetId)) {
                return i;
            }
        }
        return null;
    };
    NAVD3Force.prototype.updateLink = function (update) {
        //sourceSysname-targetSysname

        var linkObject = this.findLink(update.source.id, update.target.id);

        linkObject.data = update;
    };

    return NAVD3Force;
});
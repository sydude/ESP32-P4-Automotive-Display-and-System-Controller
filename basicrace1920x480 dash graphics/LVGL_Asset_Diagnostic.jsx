#target illustrator

(function () {
    var target = "LVGL_TEST_ASSET";
    var stage = "opening the active document";
    var missing = { status: "not_exposed" };

    function errorInfo(error) {
        return { status: "read_error", message: String(error) };
    }

    function isReadError(object) {
        try { return object && object.status === "read_error"; }
        catch (ignored) { return false; }
    }

    function read(object, key) {
        try { return object[key]; } catch (error) { return errorInfo(error); }
    }

    function attempt(operation) {
        try { return operation(); } catch (error) { return errorInfo(error); }
    }

    function value(raw) {
        if (raw === undefined) return missing;
        if (raw === null || typeof raw === "string" ||
            typeof raw === "boolean" || typeof raw === "number") return raw;
        if (isReadError(raw)) return raw;
        if (raw instanceof Array) {
            var result = [];
            for (var i = 0; i < raw.length; i++) result.push(value(raw[i]));
            return result;
        }
        if (raw instanceof File || raw instanceof Folder) return raw.fsName;
        if (typeof raw === "function") return { status: "method" };
        try {
            if (raw.reflect.name === "Enumerator") return String(raw);
        } catch (ignored) {}
        return { status: "host_object", type: read(raw, "typename") || typeof raw };
    }

    function inspect(object, keys) {
        var result = { properties: {}, reflectedMethods: [] };
        var names = keys ? keys.split(" ") : [];
        try {
            var reflected = object.reflect.properties;
            for (var i = 0; i < reflected.length; i++) {
                var name = reflected[i].name;
                if (name !== "__proto__" && name !== "prototype" &&
                    name !== "constructor" && name !== "reflect") names.push(name);
            }
            var methods = object.reflect.methods;
            for (var j = 0; j < methods.length; j++) {
                result.reflectedMethods.push(methods[j].name);
            }
        } catch (error) { result.reflectionError = errorInfo(error); }
        for (var k = 0; k < names.length; k++) {
            if (!Object.prototype.hasOwnProperty.call(result.properties, names[k])) {
                try { result.properties[names[k]] = value(read(object, names[k])); }
                catch (error) { result.properties[names[k]] = errorInfo(error); }
            }
        }
        return result;
    }

    function collection(items, visit) {
        if (items === undefined || items === null) return value(items);
        if (isReadError(items)) return items;
        var length = read(items, "length");
        if (typeof length !== "number") return { length: value(length) };
        var rows = [];
        for (var i = 0; i < length; i++) {
            try { rows.push(visit(items[i], i)); }
            catch (error) { rows.push({ index: i, error: errorInfo(error) }); }
        }
        return rows;
    }

    function identity(object) {
        if (!object || isReadError(object)) return value(object);
        return {
            type: value(read(object, "typename")),
            name: value(read(object, "name")),
            uuid: value(read(object, "uuid")),
            zOrderPosition: value(read(object, "zOrderPosition"))
        };
    }

    function ancestors(item) {
        var result = [];
        var parent = read(item, "parent");
        while (parent && !isReadError(parent) && result.length < 256) {
            result.push(identity(parent));
            if (read(parent, "typename") === "Document") break;
            parent = read(parent, "parent");
        }
        if (parent && isReadError(parent)) result.push(parent);
        return result;
    }

    function layers(items) {
        return collection(items, function (layer, index) {
            var row = inspect(layer, "typename name visible locked printable opacity zOrderPosition color");
            row.index = index;
            row.layers = layers(read(layer, "layers"));
            return row;
        });
    }

    function pageItem(item, index) {
        var row = inspect(item, "typename name uuid hidden locked selected editable note position left top width height geometricBounds visibleBounds controlBounds zOrderPosition opacity");
        row.index = index;
        row.ancestors = ancestors(item);
        var nested = "matrix boundingBox fillColor strokeColor pathPoints pathItems tags textPath".split(" ");
        for (var i = 0; i < nested.length; i++) {
            var key = nested[i];
            var raw = read(item, key);
            if (raw === undefined || raw === null) continue;
            if (isReadError(raw)) {
                row[key] = raw;
            } else if (key === "pathItems") {
                row[key] = collection(raw, identity);
            } else if (key === "pathPoints" || key === "tags") {
                row[key] = collection(raw, function (entry) {
                    return inspect(entry, key === "tags" ? "name value" :
                        "anchor leftDirection rightDirection pointType");
                });
            } else if (key === "matrix") {
                row[key] = inspect(raw, "mValueA mValueB mValueC mValueD mValueTX mValueTY");
            } else if (key === "textPath") {
                row[key] = inspect(raw, "geometricBounds visibleBounds position closed");
            } else if (typeof raw === "object" && !(raw instanceof Array)) {
                row[key] = inspect(raw);
            } else {
                row[key] = value(raw);
            }
        }
        return row;
    }

    function assetEntry(asset, index) {
        var row = inspect(asset, "typename assetID assetName");
        row.index = index;
        row.fieldProbes = {};
        var fields = "name id source sourceItems items pageItems members layers groups bounds geometricBounds visibleBounds controlBounds position width height artboard artboardIndex exportOptions exportSettings formats scales resolution".split(" ");
        for (var i = 0; i < fields.length; i++) {
            var key = fields[i];
            var raw = read(asset, key);
            try {
                row.fieldProbes[key] = raw === undefined ? missing :
                    raw && isReadError(raw) ? raw :
                    { status: "observed", value: value(raw) };
                if (raw && typeof raw === "object" && typeof read(raw, "length") === "number" &&
                    !(raw instanceof Array)) {
                    row.fieldProbes[key].entries = collection(raw, identity);
                }
            } catch (error) { row.fieldProbes[key] = errorInfo(error); }
        }
        return row;
    }

    // ExtendScript installations may lack the native JSON object.
    function quote(text) {
        return '"' + text.replace(/["\\\u0000-\u001f\u007f-\uffff]/g, function (ch) {
            return "\\u" + ("0000" + ch.charCodeAt(0).toString(16)).slice(-4);
        }) + '"';
    }

    function json(data, indent) {
        if (data === null || data === undefined) return "null";
        if (typeof data === "string") return quote(data);
        if (typeof data === "number") return isFinite(data) ? String(data) : quote(String(data));
        if (typeof data === "boolean") return String(data);
        var array = data instanceof Array;
        var parts = [];
        var next = indent + "  ";
        if (array) {
            for (var i = 0; i < data.length; i++) parts.push(next + json(data[i], next));
        } else {
            for (var key in data) {
                if (Object.prototype.hasOwnProperty.call(data, key)) {
                    parts.push(next + quote(key) + ": " + json(data[key], next));
                }
            }
        }
        return (array ? "[" : "{") +
            (parts.length ? "\n" + parts.join(",\n") + "\n" + indent : "") +
            (array ? "]" : "}");
    }

    function writeReport(file, contents) {
        file.encoding = "UTF-8";
        if (!file.open("w")) throw Error(file.error || "Could not open report file.");
        try {
            if (!file.write(contents)) throw Error(file.error || "Could not write report.");
        } finally {
            if (!file.close()) throw Error(file.error || "Could not close report.");
        }
    }

    try {
        if (!app.documents.length) {
            alert("Open the Illustrator document containing " + target + " first.");
            return;
        }

        var doc = app.activeDocument;
        var assets = read(doc, "assets");
        var artboards = read(doc, "artboards");
        stage = "reading document metadata";
        var report = {
            schemaVersion: 1,
            illustratorVersion: app.version,
            targetAssetName: target,
            geometry: "Raw Illustrator DOM coordinates in points. Bounds are [left, top, right, bottom].",
            coordinateSystem: value(read(app, "coordinateSystem")),
            document: inspect(doc, "typename name fullName path saved width height geometricBounds visibleBounds rulerOrigin pageOrigin rulerUnits documentColorSpace"),
            activeArtboardIndex: attempt(function () { return artboards.getActiveArtboardIndex(); }),
            artboards: collection(artboards, function (artboard, index) {
                var row = inspect(artboard, "typename name artboardRect rulerOrigin rulerPAR showCenter showCrossHairs showSafeAreas");
                row.index = index;
                return row;
            }),
            layers: attempt(function () { return layers(read(doc, "layers")); }),
            pageItems: attempt(function () { return collection(read(doc, "pageItems"), pageItem); }),
            selection: collection(read(doc, "selection"), identity),
            assetExport: {
                documentedAssetProperties: ["assetID", "assetName", "parent", "typename"],
                fieldStatus: {
                    observed: "The getter returned a value, including null or false.",
                    not_exposed: "This property probe returned undefined in this host.",
                    read_error: "The property getter threw an exception.",
                    host_object: "The getter returned a host object summarized by type."
                },
                membershipNote: "Document inventory and selection are independent observations. Asset membership requires an asset-level reference.",
                entries: attempt(function () { return collection(assets, assetEntry); }),
                targetMatchIndices: []
            }
        };

        var entries = report.assetExport.entries;
        if (entries instanceof Array) {
            var failures = false;
            for (var i = 0; i < entries.length; i++) {
                var props = entries[i].properties;
                if (!props || typeof props.assetName !== "string") failures = true;
                else if (props.assetName === target) report.assetExport.targetMatchIndices.push(i);
            }
            report.assetExport.targetStatus = report.assetExport.targetMatchIndices.length ?
                "found" : failures ? "indeterminate" : "not_found";
        } else {
            report.assetExport.targetStatus = "asset_collection_unavailable";
        }

        stage = "encoding the JSON report";
        var contents = json(report, "") + "\n";
        stage = "saving the JSON report";
        var source = read(doc, "fullName");
        var destination;
        if (source instanceof File && source.exists) {
            var stem = doc.name.replace(/\.[^.]+$/, "") + ".asset-diagnostic";
            destination = new File(source.parent.fsName + "/" + stem + ".json");
            var suffix = 2;
            while (destination.exists) {
                destination = new File(source.parent.fsName + "/" + stem + "-" + suffix++ + ".json");
            }
            try {
                writeReport(destination, contents);
            } catch (error) {
                alert("Could not save beside the document. Choose another location.\n" + error);
                destination = null;
            }
        }
        if (!destination) {
            destination = File.saveDialog("Save the Asset Export diagnostic JSON");
            if (!destination) return;
            if (!/\.json$/i.test(destination.name)) destination = new File(destination.fsName + ".json");
            if (destination.exists) {
                alert("That JSON file already exists. Run the script again and choose a new filename.");
                return;
            }
            writeReport(destination, contents);
        }
        alert("Diagnostic saved to:\n" + destination.fsName +
            "\n\n" + target + ": " + report.assetExport.targetStatus);
    } catch (error) {
        alert("Asset Export diagnostic failed while " + stage + ":\n" + error +
            (error.line ? "\nScript line: " + error.line : ""));
    }
}());

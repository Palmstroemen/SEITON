.pragma library

function trimTrailingSlash(path) {
    var value = String(path || "")
    if (value.length > 1 && value.endsWith("/")) {
        return value.slice(0, -1)
    }
    return value
}

function fromFileUrl(path) {
    var value = String(path || "").trim()
    if (value.indexOf("file://") !== 0) {
        return value
    }
    var raw = value.slice(7)
    if (raw.indexOf("/") === 0) {
        return raw
    }
    var slash = raw.indexOf("/")
    if (slash >= 0) {
        return raw.slice(slash)
    }
    return raw
}

function toFileUrl(path) {
    if (String(path || "").indexOf("file://") === 0) return path
    return "file://" + path
}

function normalizeFsPath(path) {
    var value = String(path || "").trim()
    if (value.length === 0) {
        return ""
    }
    if (value.indexOf("file://") === 0) {
        var raw = fromFileUrl(value)
        try {
            value = decodeURIComponent(raw)
        } catch (e) {
            value = raw
        }
    }
    return trimTrailingSlash(value)
}

function basename(path) {
    var text = String(path || "")
    if (text.length === 0) {
        return "(unknown)"
    }
    var parts = text.split("/")
    return parts.length > 0 ? (parts[parts.length - 1] || text) : text
}

// Where one stands after paths were deleted (review 2026-11-18, X3): the place itself, or the
// parent of the removed folder that held it - never a folder that is gone.
function placeAfterRemoval(place, removed) {
    var current = trimTrailingSlash(normalizeFsPath(place))
    var list = removed || []
    for (var i = 0; i < list.length; i++) {
        var gone = trimTrailingSlash(normalizeFsPath(list[i]))
        if (gone.length === 0) continue
        if (current === gone || current.indexOf(gone + "/") === 0) {
            var slash = gone.lastIndexOf("/")
            current = slash > 0 ? gone.slice(0, slash) : "/"
        }
    }
    return current
}

// Where one stands after entries moved or were renamed (X3): moves are {source, destination};
// standing in (or below) a moved folder, one goes along with it.
function placeAfterMove(place, moves) {
    var current = trimTrailingSlash(normalizeFsPath(place))
    var list = moves || []
    for (var i = 0; i < list.length; i++) {
        var move = list[i] || {}
        var source = trimTrailingSlash(normalizeFsPath(move.source))
        var destination = trimTrailingSlash(normalizeFsPath(move.destination))
        if (source.length === 0 || destination.length === 0) continue
        if (current === source || current.indexOf(source + "/") === 0) {
            current = destination + current.slice(source.length)
        }
    }
    return current
}

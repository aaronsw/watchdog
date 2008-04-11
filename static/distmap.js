function distmap(element_id, multipolygon) {
    window.onload = function() { //@@ replace with jquery
    	var map = new GMap2(document.getElementById(element_id));
    	map.addControl(new GSmallZoomControl())
    	var poly, mypoly, coordinates
    	var minlat = Infinity
    	var minlng = Infinity
    	var maxlat = -Infinity
    	var maxlng = -Infinity
        for (mypoly in multipolygon['coordinates']) {
            mypoly = multipolygon['coordinates'][mypoly]
            coordinates = []
            for (coord in mypoly) {
                coord = mypoly[coord]
                coordinates.push(new GLatLng(coord[1], coord[0]))
            }
            poly = new GPolygon(coordinates, '#520099', 2, 0.5, '#B866FF', 0.5)
            map.addOverlay(poly)
            minlat = Math.min(minlat, poly.getBounds().getSouthWest().lat())
            maxlat = Math.max(maxlat, poly.getBounds().getNorthEast().lat())
            minlng = Math.min(minlng, poly.getBounds().getSouthWest().lng())
            maxlng = Math.max(maxlng, poly.getBounds().getNorthEast().lng())
        }
        var bounds = new GLatLngBounds(new GLatLng(minlat, minlng), new GLatLng(maxlat, maxlng))
        map.setCenter(bounds.getCenter(), map.getBoundsZoomLevel(bounds))
    }
}

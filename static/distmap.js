function distmap(element_id, districtid) {
    window.onload = function() { //@@ not right
    	var WMS_URL = 'http://www.govtrack.us/perl/wms-cd.cgi?';
        var G_MAP_LAYER_FILLED = createWMSTileLayer(WMS_URL, "cd-filled,district=" + districtid, null, "image/gif", null, null, null, .25);
        var G_MAP_LAYER_OUTLINES = createWMSTileLayer(WMS_URL, "cd-outline,district=" + districtid, null, "image/gif", null, null, null, .66, "Data from GovTrack.us");
        var G_MAP_OVERLAY = createWMSOverlayMapType([G_MAP_TYPE.getTileLayers()[0], G_MAP_LAYER_FILLED, G_MAP_LAYER_OUTLINES], "Overlay");

    	var map = new GMap2(document.getElementById(element_id));
        map.addControl(new GSmallMapControl());
        map.addControl(new GScaleControl());
    	map.enableContinuousZoom()
    	//map.removeMapType(G_MAP_TYPE);
	    map.removeMapType(G_SATELLITE_TYPE);
        map.addMapType(G_MAP_OVERLAY);
        //map.addControl(new GMapTypeControl());
        //map.addControl(new GOverviewMapControl());
        map.setCenter(new GLatLng(39.813613,-98.555903),3);
        map.setMapType(G_MAP_OVERLAY);
    }
}

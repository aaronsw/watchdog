function distmap(element_id, districtid)
    window.onload = function() { //@@ not right
        districtid = districtid.replace('-', '')
        
        var WMS_URL = 'http://www.govtrack.us/perl/wms-cd.cgi?';
        var G_MAP_LAYER_FILLED = createWMSTileLayer(WMS_URL, "cd-filled,district=" + districtid, null, "image/gif", null, null, null, .25);
	    var G_MAP_LAYER_OUTLINES = createWMSTileLayer(WMS_URL, "cd-outline,district= + districtid", null, "image/gif", null, null, null, .66, "Data from GovTrack.us");
	    var G_MAP_OVERLAY = createWMSOverlayMapType([G_MAP_TYPE.getTileLayers()[0], G_MAP_LAYER_FILLED, G_MAP_LAYER_OUTLINES], "Overlay");

    	document.getElementById("googlemap").style.height = (screen.height - 485) + "px";
    	var map = new GMap2(document.getElementById("googlemap"));
    	map.enableContinuousZoom()
    	//map.removeMapType(G_MAP_TYPE);
    	map.removeMapType(G_SATELLITE_TYPE);
    	map.addMapType(G_MAP_OVERLAY);
    	map.addControl(new GLargeMapControl());
    	//map.addControl(new GMapTypeControl());
    	//map.addControl(new GOverviewMapControl());
    	map.addControl(new GScaleControl());
    	map.setMapType(G_MAP_OVERLAY);
}
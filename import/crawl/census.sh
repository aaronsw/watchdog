#!/bin/bash
#DEBUG="echo"

DATADIR="${PWD}/../../data/crawl/census/"

STATES="Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware District_of_Columbia Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New_Hampshire New_Jersey New_Mexico New_York North_Carolina North_Dakota Ohio Oklahoma Oregon Pennsylvania Puerto_Rico Rhode_Island South_Carolina South_Dakota Tennessee Texas Utah Vermont Virginia Washington West_Virginia Wisconsin Wyoming"


function download {
	# Downloads about: 3.8G
	echo "Download the files..."
	# The main census data for entire nation
	OPTS="-nc -nd"
	cd ${DATADIR}
	${DEBUG} wget ${OPTS} ftp://ftp.census.gov/census_2000/datasets/Summary_File_1/0Final_National/all_0Final_National.zip
	${DEBUG} wget ${OPTS} ftp://ftp.census.gov/census_2000/datasets/Summary_File_3/0_National/all_0_National-part1.zip
	${DEBUG} wget ${OPTS} ftp://ftp.census.gov/census_2000/datasets/Summary_File_3/0_National/all_0_National-part2.zip

	# The main census data for congressional districts
	${DEBUG} wget ${OPTS} ftp://ftp2.census.gov/census_2000/datasets/Summary_File_Extracts/110_Congressional_Districts/110_CD_HundredPercent/United_States/sl500-in-sl010-us_h10.zip
	${DEBUG} wget ${OPTS} ftp://ftp2.census.gov/census_2000/datasets/Summary_File_Extracts/110_Congressional_Districts/110_CD_Sample/United_States/sl500-in-sl010-us_s10.zip
	cd -

	# The meta data about the formats
	OPTS="-nc -nd"
	cd ${DATADIR}census_data/table_layouts/
	${DEBUG} wget ${OPTS} http://www.census.gov/support/2000/SF1/SF1SAS.zip
	${DEBUG} wget ${OPTS} http://www.census.gov/support/2000/SF3/SF3SAS.zip
	cd -

	# Data for states population down to the the block level
	OPTS="-nc -nd"
	cd ${DATADIR}census_data/by_state/
	for STATE in ${STATES}; do
		${DEBUG} wget ${OPTS} ftp://ftp.census.gov/census_2000/datasets/Summary_File_1/${STATE}/*geo_uf1.zip
		${DEBUG} wget ${OPTS} ftp://ftp.census.gov/census_2000/datasets/Summary_File_1/${STATE}/*00001_uf1.zip
	done
	cd -

	# Data for congrssional districts population down to the the block^H^H^H^H^Htract level
	OPTS="-nc -nd"
	BASE_URL="ftp://ftp2.census.gov/census_2000/datasets/110_Congressional_Districts/"
	cd ${DATADIR}census_data/congress/
	for STATE in ${STATES}; do
		${DEBUG} wget ${OPTS} ${BASE_URL}110_CD_HundredPercent/${STATE}/*00001_h10.zip ${BASE_URL}110_CD_HundredPercent/${STATE}/*geo_h10.zip ;
	done
	cd -

	# Geo data for mapnik
	OPTS="-nc -nd"
	cd ${DATADIR}geo/
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/zt/z500shp/zt99_d00_shp.zip
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/co/co00shp/co99_d00_shp.zip
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/st/st00shp/st99_d00_shp.zip
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/cd/cd110shp/cd99_110_shp.zip
	cd -

	# Geo data for calculating location center, probably could do with the shp files, but govtrack_gis uses these
	OPTS="-nc -nd"
	cd ${DATADIR}
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/st/st00ascii/st99_d00_ascii.zip
	${DEBUG} wget ${OPTS} http://www.census.gov/geo/cob/bdy/cd/cd110ascii/cd99_110_ascii.zip
	cd -
}

function extractCurrent {
	for Z in *.zip ; do ${DEBUG} unzip -x -o "$Z" && rm "$Z" ; done
}

function extractAll {
	# Extracted is arround 30G
	echo "Extract the files..."
	ZIPDIR=${PWD}
	${DEBUG} unzip -x -o ${ZIPDIR}/cd99_110_ascii.zip &&
	${DEBUG} unzip -x -o ${ZIPDIR}/st99_d00_ascii.zip &&
	cd census_data/ &&
		${DEBUG} unzip -x -o ${ZIPDIR}/all_0Final_National.zip &&
		${DEBUG} unzip -x -o ${ZIPDIR}/all_0_National-part1.zip &&
		${DEBUG} unzip -x -o ${ZIPDIR}/all_0_National-part2.zip &&
		cd congress/ &&
			${DEBUG} unzip -x -o ${ZIPDIR}/sl500-in-sl010-us_h10.zip &&
			${DEBUG} unzip -x -o ${ZIPDIR}/sl500-in-sl010-us_s10.zip &&
			cd ../ &&
		cd ../ &&
	cd geo/ &&
		for Z in *.zip; do ${DEBUG} unzip -x -o ${Z}; done
		cd ../
}


cd ${DATADIR} && 
mkdir -p census_data/{table_layouts,congress,by_state} geo/
download
extractAll

